"""
RocketReach Web Crawler
Tất cả logic Playwright cho RocketReach: login, search, pagination, extraction
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlencode, urlparse, parse_qs

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from asgiref.sync import sync_to_async

from .models import RocketReachContact

logger = logging.getLogger(__name__)


class RocketReachWebCrawler:
    """Web crawler for RocketReach using Playwright - tất cả logic Playwright"""
    
    def __init__(self, headless: bool = True, max_pages: int = 10, page_size: int = 20, nav_timeout_sec: int = 60, start_page: int = 1):
        self.headless = headless
        self.max_pages = max_pages
        self.page_size = page_size  # desired items per page
        self.base_start = start_page  # starting index from URL (start=)
        self.nav_timeout_ms = max(10, nav_timeout_sec) * 1000
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        self.page = await context.new_page()
        # Set generous timeouts to handle Cloudflare/slow loads
        self.page.set_default_navigation_timeout(self.nav_timeout_ms)
        self.page.set_default_timeout(self.nav_timeout_ms)
        
        # Add stealth measures
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Cleanup browser resources"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    async def _snapshot(self, stage: str, include_html: bool = False):
        """Save a screenshot and optionally the full HTML for debugging."""
        try:
            screenshot_path = f"rocketreach_{stage}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Snapshot saved: {screenshot_path}")
        except Exception as e:
            logger.debug(f"Snapshot screenshot failed for {stage}: {e}")
        if include_html:
            try:
                html = await self.page.content()
                html_path = f"rocketreach_{stage}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info(f"HTML saved: {html_path}")
            except Exception as e:
                logger.debug(f"Snapshot HTML failed for {stage}: {e}")
    
    async def login(self) -> bool:
        """Login to RocketReach - with network interception"""
        try:
            email = 'santiago.wolfbrothers.ads@gmail.com'
            password = 'Hgiang2004@'
            
            logger.info(f"Attempting login with email: {email}")
            
            # Setup network interception
            login_requests = []
            
            async def handle_request(request):
                if 'login' in request.url.lower() and request.method == 'POST':
                    login_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': request.headers,
                        'post_data': request.post_data
                    })
                    logger.info(f'Login request intercepted: {request.url}')
                    logger.info(f'Headers: {dict(request.headers)}')
                    logger.info(f'Post data: {request.post_data}')
            
            self.page.on('request', handle_request)
            
            # Navigate to login page with retries
            login_url = 'https://rocketreach.co/login'
            last_err = None
            for attempt in range(3):
                try:
                    await self.page.goto(login_url, wait_until='domcontentloaded')
                    # extra wait to stabilize network
                    await self.page.wait_for_load_state('networkidle')
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(f'Goto login attempt {attempt+1} failed: {e}. Retrying...')
                    await self.page.wait_for_timeout(2000)
            if last_err:
                raise last_err
            
            # Wait for Cloudflare protection
            try:
                await self.page.wait_for_function(
                    "() => !document.title.includes('Just a moment') && !document.body.innerText.includes('Checking your browser')",
                    timeout=self.nav_timeout_ms
                )
                logger.info('Cloudflare protection passed')
            except:
                logger.warning('Cloudflare protection may still be active')
            
            # Debug: Take screenshot and analyze page
            await self._debug_page_state("before_form_fill")
            
            # Fill login form with improved logic
            await self._fill_login_form(email, password)
            
            # Debug: Check form state after filling
            await self._debug_form_state("after_form_fill")
            
            # Handle reCAPTCHA
            await self._handle_recaptcha()
            
            # Debug: Check form state after reCAPTCHA
            await self._debug_form_state("after_recaptcha")
            
            # Submit form with improved logic
            await self._submit_form()
            
            # Wait for redirect
            await self.page.wait_for_function(
                "() => window.location.href.includes('/dashboard') || window.location.href.includes('/login')",
                timeout=15000
            )
            
            # Debug: Check final state
            await self._debug_page_state("after_submit")
            
            # Log intercepted requests
            if login_requests:
                logger.info(f'Intercepted {len(login_requests)} login requests')
                for i, req in enumerate(login_requests):
                    logger.info(f'Request {i+1}: {req["method"]} {req["url"]}')
                    logger.info(f'Headers: {req["headers"]}')
                    logger.info(f'Post data: {req["post_data"]}')
            else:
                logger.warning('No login requests intercepted - form may not have been submitted')
            
            # Debug: Check current URL and page content
            current_url = self.page.url
            logger.info(f'Current URL after login attempt: {current_url}')
            
            # Check for error messages
            try:
                error_elements = await self.page.query_selector_all('.error, [class*="error"], .alert-danger, .invalid-feedback')
                if error_elements:
                    for element in error_elements:
                        error_text = await element.inner_text()
                        if error_text.strip():
                            logger.error(f'Login error message: {error_text.strip()}')
            except:
                pass
            
            if '/dashboard' in current_url:
                logger.info('Successfully logged into RocketReach')
                return True
            else:
                logger.error(f'Login failed - current URL: {current_url}')
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def _handle_recaptcha(self):
        """Handle reCAPTCHA and Angular validation - improved logic"""
        try:
            # Wait for potential reCAPTCHA
            await self.page.wait_for_timeout(3000)
            
            # Check for reCAPTCHA elements
            recaptcha_selectors = [
                '.g-recaptcha',
                'iframe[src*="recaptcha"]',
                '[class*="recaptcha"]',
                'div[data-sitekey]'
            ]
            
            recaptcha_found = False
            for selector in recaptcha_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    recaptcha_found = True
                    break
            
            # Always handle reCAPTCHA and Angular validation
            logger.info('Handling reCAPTCHA and Angular validation...')
            
            # Method 1: Try to execute reCAPTCHA programmatically
            if recaptcha_found:
                await self.page.evaluate("""
                    if (typeof grecaptcha !== 'undefined') {
                        try {
                            grecaptcha.execute('6Le8JXkUAAAAABWqhg7ud4UjL6yCBDirQhWh5CHD', {action: 'submit'}).then(function(token) {
                                console.log('reCAPTCHA token obtained:', token);
                                const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                                if (textarea) {
                                    textarea.value = token;
                                }
                                if (window.PLY_Service_RecaptchaV3Service_loaded) {
                                    window.PLY_Service_RecaptchaV3Service_loaded();
                                }
                            });
                        } catch(e) {
                            console.log('reCAPTCHA execute failed:', e);
                        }
                    }
                """)
            
            # Method 2: Force set reCAPTCHA ready and fix Angular validation
            await self.page.evaluate("""
                // Set recaptchaReady to true
                window.recaptchaReady = true;
                
                // Set fake token in reCAPTCHA field
                const recaptchaField = document.querySelector('input[name="recaptcha"]');
                if (recaptchaField) {
                    recaptchaField.value = 'fake_recaptcha_token_for_testing';
                }
                
                // Fix Angular form validation
                const form = document.querySelector('form');
                if (form && window.angular) {
                    const scope = window.angular.element(form).scope();
                    if (scope) {
                        // Force form to be valid
                        scope.$valid = true;
                        scope.$invalid = false;
                        scope.$pristine = false;
                        scope.$dirty = true;
                        
                        // Set processing to false
                        scope.processing = false;
                        
                        // Apply changes
                        scope.$apply();
                    }
                }
                
                // Force enable the submit button
                const button = document.querySelector('button[type="submit"]');
                if (button) {
                    button.disabled = false;
                    button.removeAttribute('disabled');
                    button.removeAttribute('ng-disabled');
                    button.setAttribute('ng-disabled', 'false');
                    
                    // Update button classes to remove disabled state
                    button.classList.remove('disabled');
                    button.classList.add('enabled');
                }
                
                // Trigger any reCAPTCHA callbacks
                if (window.PLY_Service_RecaptchaV3Service_loaded) {
                    window.PLY_Service_RecaptchaV3Service_loaded();
                }
                
                console.log('reCAPTCHA and Angular validation bypass completed');
            """)
            
            await self.page.wait_for_timeout(2000)
            logger.info('reCAPTCHA and Angular validation handling completed')
            
        except Exception as e:
            logger.warning(f'reCAPTCHA handling failed: {e}')
    
    async def _fill_login_form(self, email: str, password: str):
        """Fill login form with improved logic"""
        try:
            # Wait for form to be ready
            await self.page.wait_for_selector('input[type="email"], input[type="password"]', timeout=10000)
            
            # Try multiple selectors for email input
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
                'input[id*="email" i]',
                'input[class*="email" i]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.fill(selector, '')
                    await self.page.type(selector, email)
                    
                    # Trigger events
                    await self.page.evaluate(f"""
                        const field = document.querySelector('{selector}');
                        if (field) {{
                            field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            field.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            field.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        }}
                    """)
                    
                    email_filled = True
                    logger.info(f'Email filled with selector: {selector}')
                    break
                except:
                    continue
            
            if not email_filled:
                raise Exception('Could not find email input field')
            
            # Try multiple selectors for password input
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="Password" i]',
                'input[id*="password" i]',
                'input[class*="password" i]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    await self.page.fill(selector, '')
                    await self.page.type(selector, password)
                    
                    # Trigger events
                    await self.page.evaluate(f"""
                        const field = document.querySelector('{selector}');
                        if (field) {{
                            field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            field.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            field.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        }}
                    """)
                    
                    password_filled = True
                    logger.info(f'Password filled with selector: {selector}')
                    break
                except:
                    continue
            
            if not password_filled:
                raise Exception('Could not find password input field')
            
            # Wait a bit for form validation
            await self.page.wait_for_timeout(1000)
            
            # Force set values using JavaScript
            await self.page.evaluate(f"""
                const emailField = document.querySelector('input[type="email"]');
                const passwordField = document.querySelector('input[type="password"]');
                
                if (emailField) {{
                    emailField.value = '{email}';
                    emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    emailField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                }}
                
                if (passwordField) {{
                    passwordField.value = '{password}';
                    passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                }}
            """)
            
            # Wait for validation
            await self.page.wait_for_timeout(1000)
            
            # Verify fields are filled
            email_value = await self.page.input_value('input[type="email"]')
            password_value = await self.page.input_value('input[type="password"]')
            
            logger.info(f'Email field value: {email_value[:10]}...')
            logger.info(f'Password field value: {"*" * len(password_value)}')
            
            if not email_value or not password_value:
                raise Exception('Form fields not properly filled')
            
        except Exception as e:
            logger.error(f'Failed to fill login form: {e}')
            raise
    
    async def _debug_page_state(self, stage: str):
        """Debug page state at different stages"""
        try:
            # Take screenshot
            await self.page.screenshot(path=f'rocketreach_debug_{stage}.png')
            logger.info(f'Debug screenshot saved: rocketreach_debug_{stage}.png')
            
            # Get page title and URL
            title = await self.page.title()
            url = self.page.url
            logger.info(f'Debug {stage} - Title: {title}, URL: {url}')
            
            # Check for form elements
            form_elements = await self.page.query_selector_all('form')
            logger.info(f'Debug {stage} - Found {len(form_elements)} form elements')
            
            for i, form in enumerate(form_elements):
                form_html = await form.inner_html()
                logger.info(f'Debug {stage} - Form {i+1} HTML: {form_html[:200]}...')
            
        except Exception as e:
            logger.warning(f'Debug {stage} failed: {e}')
    
    async def _debug_form_state(self, stage: str):
        """Debug form state and validation"""
        try:
            # Check email field
            email_field = await self.page.query_selector('input[type="email"]')
            if email_field:
                email_value = await email_field.input_value()
                email_disabled = await email_field.is_disabled()
                email_required = await email_field.get_attribute('required')
                logger.info(f'Debug {stage} - Email field: value="{email_value[:10]}...", disabled={email_disabled}, required={email_required}')
            else:
                logger.warning(f'Debug {stage} - No email field found')
            
            # Check password field
            password_field = await self.page.query_selector('input[type="password"]')
            if password_field:
                password_value = await password_field.input_value()
                password_disabled = await password_field.is_disabled()
                password_required = await password_field.get_attribute('required')
                logger.info(f'Debug {stage} - Password field: value={"*" * len(password_value)}, disabled={password_disabled}, required={password_required}')
            else:
                logger.warning(f'Debug {stage} - No password field found')
            
            # Check submit button
            submit_button = await self.page.query_selector('button[type="submit"]')
            if submit_button:
                button_disabled = await submit_button.is_disabled()
                button_text = await submit_button.inner_text()
                button_ng_disabled = await submit_button.get_attribute('ng-disabled')
                logger.info(f'Debug {stage} - Submit button: disabled={button_disabled}, text="{button_text}", ng-disabled="{button_ng_disabled}"')
            else:
                logger.warning(f'Debug {stage} - No submit button found')
            
            # Check for validation errors
            error_elements = await self.page.query_selector_all('.error, [class*="error"], .alert-danger, .invalid-feedback, .text-danger, [class*="invalid"]')
            if error_elements:
                logger.info(f'Debug {stage} - Found {len(error_elements)} error elements')
                for i, element in enumerate(error_elements):
                    error_text = await element.inner_text()
                    if error_text.strip():
                        logger.info(f'Debug {stage} - Error {i+1}: {error_text.strip()}')
            else:
                logger.info(f'Debug {stage} - No validation errors found')
            
            # Check Angular scope variables
            try:
                scope_data = await self.page.evaluate("""
                    () => {
                        const form = document.querySelector('form');
                        if (form && window.angular) {
                            const scope = window.angular.element(form).scope();
                            return {
                                processing: scope ? scope.processing : 'no scope',
                                recaptchaReady: window.recaptchaReady,
                                formValid: scope ? scope.$valid : 'no scope',
                                formInvalid: scope ? scope.$invalid : 'no scope'
                            };
                        }
                        return {
                            processing: 'no angular',
                            recaptchaReady: window.recaptchaReady,
                            formValid: 'no angular',
                            formInvalid: 'no angular'
                        };
                    }
                """)
                logger.info(f'Debug {stage} - Angular scope: {scope_data}')
            except Exception as e:
                logger.warning(f'Debug {stage} - Angular scope check failed: {e}')
            
        except Exception as e:
            logger.warning(f'Debug {stage} form state failed: {e}')
    
    async def _submit_form(self):
        """Submit login form with improved CSRF and validation handling"""
        try:
            # Get CSRF token
            csrf_token = await self.page.evaluate("""
                () => {
                    const tokenField = document.querySelector('input[name="csrfmiddlewaretoken"]');
                    return tokenField ? tokenField.value : null;
                }
            """)
            logger.info(f'CSRF token: {csrf_token[:20] if csrf_token else "None"}...')
            
            # Method 1: Try native form submission (bypass Angular)
            try:
                await self.page.evaluate("""
                    () => {
                        const form = document.querySelector('form');
                        if (form) {
                            // Create a new form element to bypass Angular
                            const newForm = document.createElement('form');
                            newForm.method = form.method;
                            newForm.action = form.action;
                            newForm.style.display = 'none';
                            
                            // Copy all inputs
                            const inputs = form.querySelectorAll('input');
                            inputs.forEach(input => {
                                const newInput = document.createElement('input');
                                newInput.type = input.type;
                                newInput.name = input.name;
                                newInput.value = input.value;
                                newForm.appendChild(newInput);
                            });
                            
                            // Add to DOM and submit
                            document.body.appendChild(newForm);
                            newForm.submit();
                        }
                    }
                """)
                logger.info('Form submitted via native form submission')
                await self.page.wait_for_timeout(2000)
                return
            except Exception as e:
                logger.warning(f'Native form submit failed: {e}')
            
            # Method 2: Try Angular form submission
            try:
                await self.page.evaluate("""
                    () => {
                        const form = document.querySelector('form');
                        if (form && window.angular) {
                            const scope = window.angular.element(form).scope();
                            if (scope) {
                                // Trigger form validation
                                scope.$apply();
                                
                                // Check if form is valid
                                if (scope.$valid) {
                                    // Submit form via Angular
                                    const formElement = window.angular.element(form);
                                    formElement.triggerHandler('submit');
                                } else {
                                    console.log('Form is invalid:', scope.$error);
                                }
                            }
                        }
                    }
                """)
                logger.info('Form submitted via Angular')
                await self.page.wait_for_timeout(2000)
                return
            except Exception as e:
                logger.warning(f'Angular submit failed: {e}')
            
            # Method 2: Try normal click with validation
            try:
                # Trigger validation events first
                await self.page.evaluate("""
                    () => {
                        const emailField = document.querySelector('input[type="email"]');
                        const passwordField = document.querySelector('input[type="password"]');
                        
                        if (emailField) {
                            emailField.dispatchEvent(new Event('blur', { bubbles: true }));
                            emailField.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        
                        if (passwordField) {
                            passwordField.dispatchEvent(new Event('blur', { bubbles: true }));
                            passwordField.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                """)
                
                await self.page.wait_for_timeout(1000)
                await self.page.click('button[type="submit"]')
                logger.info('Form submitted via normal click with validation')
                await self.page.wait_for_timeout(2000)
                return
            except Exception as e:
                logger.warning(f'Normal click failed: {e}')
            
            # Method 3: Force enable button and click
            try:
                await self.page.evaluate("""
                    const button = document.querySelector('button[type="submit"]');
                    if (button) {
                        button.disabled = false;
                        button.removeAttribute('disabled');
                        button.removeAttribute('ng-disabled');
                        button.setAttribute('ng-disabled', 'false');
                        button.click();
                    }
                """)
                logger.info('Form submitted via force click')
                await self.page.wait_for_timeout(2000)
                return
            except Exception as e:
                logger.warning(f'Force click failed: {e}')
            
            # Method 4: Submit form directly
            try:
                await self.page.evaluate("""
                    const form = document.querySelector('form');
                    if (form) {
                        form.submit();
                    }
                """)
                logger.info('Form submitted via form.submit()')
                await self.page.wait_for_timeout(2000)
                return
            except Exception as e:
                logger.warning(f'Form submit failed: {e}')
            
            # Method 5: Press Enter key
            try:
                await self.page.press('input[type="password"]', 'Enter')
                logger.info('Form submitted via Enter key')
                await self.page.wait_for_timeout(2000)
                return
            except Exception as e:
                logger.warning(f'Enter key failed: {e}')
            
            logger.error('All submit methods failed')
            
        except Exception as e:
            logger.error(f'Submit form failed: {e}')
    
    async def search_and_get_contact(self, keyword: str) -> Dict:
        """Search by keyword and click first "Get Contact Info" - logic từ rocketreach_web.py"""
        query_url = f"https://rocketreach.co/person?keyword={keyword}"
        logger.info(f'Searching for: {keyword} at {query_url}')
        
        await self.page.goto(query_url)
        await self.page.wait_for_load_state('networkidle')
        
        # Wait for search results to load
        try:
            await self.page.wait_for_selector('[data-testid="person-card"], .person-card, .search-result', timeout=10000)
        except:
            logger.warning('No search results found or different page structure')
            return {"success": False, "error": "no_search_results", "keyword": keyword}

        # Look for "Get Contact Info" buttons with multiple selectors
        button_selectors = [
            'button:has-text("Get Contact Info")',
            'button:has-text("Get Contact")',
            '[data-testid="get-contact-button"]',
            '.get-contact-button',
            'button[class*="contact"]'
        ]
        
        buttons = []
        for selector in button_selectors:
            try:
                found_buttons = await self.page.locator(selector).all()
                if found_buttons:
                    buttons = found_buttons
                    logger.info(f'Found {len(buttons)} contact buttons with selector: {selector}')
                    break
            except:
                continue
                
        if not buttons:
            return {"success": False, "error": "no_get_contact_button", "keyword": keyword}

        # Click first button
        try:
            await buttons[0].click()
            logger.info('Clicked Get Contact Info button')
        except Exception as e:
            return {"success": False, "error": f"failed_to_click_button: {str(e)}", "keyword": keyword}
            
        # Wait for modal/panel to render
        await self.page.wait_for_timeout(2000)
        
        # Try multiple approaches to find emails
        emails = []
        
        # Method 1: Look for email patterns in text
        try:
            email_loc = self.page.locator('text=/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/')
            count = await email_loc.count()
            for i in range(count):
                txt = await email_loc.nth(i).inner_text()
                if txt.strip() and '@' in txt:
                    emails.append(txt.strip())
        except Exception as e:
            logger.warning(f'Method 1 failed: {e}')
        
        # Method 2: Look in specific containers
        try:
            contact_containers = await self.page.locator('.contact-info, .email-info, .contact-details, [class*="email"]').all()
            for container in contact_containers:
                text = await container.inner_text()
                email_matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
                emails.extend(email_matches)
        except Exception as e:
            logger.warning(f'Method 2 failed: {e}')
            
        # Method 3: Look for input fields with email values
        try:
            email_inputs = await self.page.locator('input[type="email"], input[value*="@"]').all()
            for input_elem in email_inputs:
                value = await input_elem.input_value()
                if value and '@' in value:
                    emails.append(value)
        except Exception as e:
            logger.warning(f'Method 3 failed: {e}')

        # Remove duplicates and clean
        emails = list(set([email.strip() for email in emails if email.strip() and '@' in email]))
        
        logger.info(f'Found {len(emails)} emails: {emails}')

        return {
            "success": True if emails else False,
            "emails": emails,
            "keyword": keyword,
            "source": query_url,
        }
    
    async def crawl_search_results(self, base_url: str) -> List[Dict]:
        """Crawl search results with pagination. If URL is a company listing,
        click 'Search Employees' first then crawl employees (people) results."""
        logger.info(f"=== STARTING CRAWL ===")
        logger.info(f"Starting crawl for: {base_url}")
        
        all_contacts = []
        current_page = 1
        
        # Read pageSize and start from base_url if present
        try:
            parsed = urlparse(base_url)
            q = parse_qs(parsed.query)
            if 'pageSize' in q and q['pageSize']:
                try:
                    self.page_size = int(q['pageSize'][0])
                except Exception:
                    pass
            if 'start' in q and q['start']:
                try:
                    self.base_start = int(q['start'][0])
                except Exception:
                    self.base_start = 1
        except Exception:
            pass
        
        # If the incoming URL is a company results page, click 'Search Employees' to pivot to people
        try:
            parsed_path = urlparse(base_url).path
            logger.warning(f"Checking URL path: {parsed_path}")
            logger.warning(f"Full URL: {base_url}")
            logger.warning(f"Company check: '/company' in '{parsed_path}' = {'/company' in parsed_path}")
            if '/company' in parsed_path:
                logger.warning('=== COMPANY CRAWL DETECTED ===')
                logger.warning(f'Detected company results URL: {base_url}')
                logger.warning('Attempting to click "Search Employees"...')
                
                # Load the company results page as provided (respect start/pageSize from URL/CLI)
                await self.page.goto(base_url)
                await self.page.wait_for_load_state('networkidle')
                # Snapshot company page to verify real HTML/DOM
                await self._snapshot('company_page', include_html=True)
                
                # Try to find and iterate all "Search Employees" buttons on the current company page
                try:
                    await self.page.wait_for_selector('button[data-px-single-search-employees="true"]', timeout=30000)
                    total_contacts_company_page = 0
                    buttons_count = len(await self.page.query_selector_all('button[data-px-single-search-employees="true"]'))
                    logger.warning(f'Company page: found {buttons_count} "Search Employees" buttons')

                    # Iterate each company on the current page
                    company_index = 0
                    processed_companies = set()  # Track processed company IDs
                    while company_index < buttons_count:
                        # Refetch buttons each loop (DOM may change after back navigation)
                        buttons = await self.page.query_selector_all('button[data-px-single-search-employees="true"]')
                        if company_index >= len(buttons):
                            logger.warning(f'Company index {company_index} exceeds available buttons {len(buttons)}, stopping')
                            break
                        
                        # Skip if button is not clickable
                        btn = buttons[company_index]
                        if not (await btn.is_visible()) or not (await btn.is_enabled()):
                            logger.warning(f'Button {company_index+1} not clickable, skipping to next')
                            company_index += 1
                            continue

                        # Extract info for logging
                        try:
                            info = await btn.evaluate('''(el) => {
                                const container = el.closest('[data-test-id="company_card_container"]');
                                const main = container ? container.querySelector('[data-test-id="company_card_main_info"]') : null;
                                const link = main ? main.querySelector('a[target="_blank"]') : null;
                                const checkbox = main ? main.querySelector('input[id^="company-selection-"]') : null;
                                const companyId = checkbox ? (checkbox.id || '').replace('company-selection-','') : '';
                                let name = '';
                                if (link) {
                                    name = (link.textContent || '').trim();
                                    if (!name) {
                                        const span = link.querySelector('span');
                                        name = span ? (span.textContent || '').trim() : '';
                                    }
                                }
                                if (!name && main) {
                                    const nameEl = main.querySelector('p.line-clamp-2.text-base.font-heavy-552');
                                    if (nameEl) {
                                        const nameLink = nameEl.querySelector('a[target="_blank"]');
                                        name = nameLink ? (nameLink.textContent || '').trim() : '';
                                    }
                                }
                                return { id: companyId, name: name || 'Unknown Company' };
                            }''')
                        except Exception:
                            info = { 'id': '', 'name': 'Unknown Company' }
                        
                        # Check if this company has already been processed
                        company_id = info.get('id', '')
                        if company_id and company_id in processed_companies:
                            logger.warning(f'Company {company_id} already processed, skipping to next')
                            company_index += 1
                            continue
                        
                        # Mark this company as processed
                        if company_id:
                            processed_companies.add(company_id)

                        logger.warning(f'=== COMPANY {company_index+1}/{buttons_count} ===')
                        logger.warning(f'Company ID: {info.get("id", "?")}')
                        logger.warning(f'Company Name: {info.get("name", "Unknown")}')
                        logger.warning(f'Processing company: {info.get("name", "Unknown")} (ID: {info.get("id", "?")})')

                        try:
                            await btn.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(100)  # Reduced
                        except Exception:
                            pass
                        try:
                            await btn.hover()
                            await self.page.wait_for_timeout(50)  # Reduced
                        except Exception:
                            pass

                        if not (await btn.is_visible()) or not (await btn.is_enabled()):
                            logger.warning('Target button not clickable, skipping company')
                            continue

                        # Wait for navigation to employees (reduced timeout)
                        try:
                            # Wait for navigation with a promise to capture the new URL
                            await self.page.wait_for_function("() => location.pathname.includes('/person')", timeout=8000)
                        except Exception:
                            logger.debug('Employees URL detection by pathname failed; relying on networkidle')
                        
                        # Click the button
                        await btn.click()
                        logger.warning('✅ Clicked "Search Employees"')
                        
                        # Wait for navigation to complete
                        await self.page.wait_for_load_state('domcontentloaded')  # Faster than networkidle
                        
                        # Log the actual URL after navigation
                        current_url = self.page.url
                        logger.warning(f'Current URL after click: {current_url}')
                        
                        # Check if URL contains company-specific parameters
                        if 'employer' not in current_url and 'company' not in current_url:
                            logger.warning('⚠️ URL does not contain company-specific parameters - button may not be working correctly')
                            # Try to manually construct the URL with company ID
                            if company_id:
                                manual_url = f"https://rocketreach.co/person?employer%5B%5D=%22{company_id}%3A{info.get('name', 'Unknown').replace(' ', '+')}%22&start=1&pageSize=100"
                                logger.warning(f'Attempting manual navigation to: {manual_url}')
                                await self.page.goto(manual_url)
                                await self.page.wait_for_load_state('domcontentloaded')
                                current_url = self.page.url
                                logger.warning(f'Manual URL result: {current_url}')
                        
                        # Skip snapshot for performance

                        # Rewrite to single-page employees with pageSize=100, preserving company-specific parameters
                        switched_url = self.page.url
                        try:
                            p = urlparse(switched_url)
                            q = parse_qs(p.query)
                            
                            # Preserve all existing parameters, only modify pageSize and start
                            q['pageSize'] = [str(100)]
                            q['start'] = ['1']
                            
                            # Keep all other parameters (especially employer[] for company-specific search)
                            new_query = urlencode(q, doseq=True)
                            employees_url = f"{p.scheme}://{p.netloc}{p.path}?{new_query}"
                            logger.warning(f'Switched to employees URL (single page): {employees_url}')
                            await self.page.goto(employees_url)
                            await self.page.wait_for_load_state('domcontentloaded')  # Faster than networkidle
                            try:
                                await self.page.wait_for_selector('[data-profile-card-id]', timeout=8000)  # Reduced timeout
                            except Exception:
                                logger.debug('Employee cards selector did not appear within timeout')
                            # Skip snapshot for performance
                        except Exception as e:
                            logger.debug(f'Failed to rewrite employees URL pageSize/start: {e}')

                        # Extract contacts from this employees page
                        try:
                            contacts_company = await self._extract_contacts_from_page(1)
                            total_contacts_company_page += len(contacts_company)
                            all_contacts.extend(contacts_company)
                            logger.warning(f'Company {company_index+1} ({info.get("name", "Unknown")}): extracted {len(contacts_company)} contacts')
                            if contacts_company:
                                for contact in contacts_company:
                                    logger.warning(f'  - {contact.get("name", "N/A")} ({contact.get("email", "N/A")})')
                        except Exception as e:
                            logger.warning(f'Extraction failed for company {company_index+1} ({info.get("name", "Unknown")}): {e}')

                        # Go back to company list page for next company
                        try:
                            # Use longer timeout and retry logic
                            for retry in range(3):
                                try:
                                    await self.page.goto(base_url, timeout=90000)  # 90s timeout
                                    await self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                                    
                                    # Wait for buttons to be available again
                                    await self.page.wait_for_selector('button[data-px-single-search-employees="true"]', timeout=10000)
                                    break
                                except Exception as retry_e:
                                    if retry == 2:
                                        raise retry_e
                                    logger.warning(f'Retry {retry+1}/3: Failed to go back to company page: {retry_e}')
                                    await self.page.wait_for_timeout(2000)
                            
                            # Skip snapshot for performance
                            logger.warning(f'Returned to company page for next company (current: {company_index+1}/{buttons_count})')
                            
                            # Debug: check if buttons are still available
                            current_buttons = await self.page.query_selector_all('button[data-px-single-search-employees="true"]')
                            logger.warning(f'After return: found {len(current_buttons)} buttons (was {buttons_count})')
                            
                            # Update buttons_count in case it changed
                            buttons_count = len(current_buttons)
                        except Exception as e:
                            logger.warning(f'Failed to go back to company page after retries: {e}')
                            break
                        
                        # Increment company index for next iteration
                        company_index += 1

                    logger.warning(f'=== END COMPANY CRAWL (companies processed: {buttons_count}, contacts found: {total_contacts_company_page}) ===')
                    # After iterating companies on this page, return accumulated contacts
                    # The company crawl is complete - no need for normal pagination
                    return all_contacts
                except Exception as e:
                    logger.warning(f'Could not pivot from company page to employees: {e}')
            else:
                logger.info(f"URL is not a company page, proceeding with normal crawl")
        except Exception as e:
            logger.debug(f'Company URL detection failed (non-blocking): {e}')
        
        while current_page <= self.max_pages:
            try:
                # Build URL with pagination
                page_url = self._build_page_url(base_url, current_page)
                logger.info(f"Crawling page {current_page}: {page_url}")
                
                # Navigate to page
                await self.page.goto(page_url)
                await self.page.wait_for_load_state('networkidle')
                
                # Wait for search results (ensure list is populated and stable)
                try:
                    await self.page.wait_for_selector('[data-profile-card-id]', timeout=15000)
                    # Wait for the number of cards to stabilize (handles incremental API rendering)
                    last_count = -1
                    stable_iterations = 0
                    for _ in range(20):  # up to ~10s (20 * 500ms)
                        cards = await self.page.query_selector_all('[data-profile-card-id]')
                        count = len(cards)
                        if count == last_count:
                            stable_iterations += 1
                        else:
                            stable_iterations = 0
                        last_count = count
                        if stable_iterations >= 4:  # ~2s stable
                            break
                        await self.page.wait_for_timeout(500)
                except:
                    logger.warning(f'No search results found on page {current_page}')
                    break
                
                # Extract contacts from current page
                page_contacts = await self._extract_contacts_from_page(current_page)
                all_contacts.extend(page_contacts)
                
                logger.info(f"Found {len(page_contacts)} contacts on page {current_page}")
                
                # Check if there's a next page
                if not await self._has_next_page():
                    logger.info("No more pages available")
                    break
                
                current_page += 1
                
                # Add delay between pages (reduced)
                await self.page.wait_for_timeout(1000)
                
            except Exception as e:
                logger.error(f"Error crawling page {current_page}: {e}")
                break
        
        logger.info(f"Total contacts found: {len(all_contacts)}")
        return all_contacts
    
    def _build_page_url(self, base_url: str, page: int) -> str:
        """Build URL for a specific page respecting start and pageSize."""
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Respect desired page size
        query_params['pageSize'] = [str(self.page_size)]
        
        # Compute start based on initial base_start and page_size
        start_index = self.base_start + (page - 1) * self.page_size
        if start_index < 1:
            start_index = 1
        query_params['start'] = [str(start_index)]
        
        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
    
    async def _has_next_page(self) -> bool:
        """Check if there's a next page available"""
        try:
            # Look for next page button or pagination indicators
            next_selectors = [
                'button:has-text("Next")',
                'button:has-text(">")',
                '.pagination .next',
                '[data-testid="next-page"]',
                'a[aria-label="Next page"]'
            ]
            
            for selector in next_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_enabled():
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    async def _extract_contacts_from_page(self, page_number: int) -> List[Dict]:
        """Extract contact information from current page - click Get Contact Info buttons first"""
        contacts = []
        
        try:
            # Find all profile cards first
            profile_cards = await self.page.query_selector_all('[data-profile-card-id]')
            logger.info(f"Found {len(profile_cards)} profile cards on page {page_number}")
            
            for i, card in enumerate(profile_cards):
                try:
                    # Wait for contact info to potentially load (don't skip too early)
                    try:
                        await card.wait_for_selector('[data-onboarding-id="main-contact-info-lookup-complete"], a[href*="mailto:"]', timeout=3000)
                    except Exception:
                        # best-effort wait
                        await self.page.wait_for_timeout(500)

                    # Click "Get Contact Info" button for this card (if present)
                    await self._click_get_contact_info(card, i + 1)
                    
                    # Wait a bit for email to load (reduced)
                    await self.page.wait_for_timeout(1000)
                    
                    # Extract contact info after clicking
                    contact_info = await self._extract_single_contact_after_click(card, page_number, i + 1)
                    if contact_info:
                        contacts.append(contact_info)
                        logger.info(f"Extracted contact {i+1}: {contact_info.get('name', 'N/A')} - {contact_info.get('email', 'N/A')}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting contact {i+1} on page {page_number}: {e}")
                    # Save card HTML snapshot for debugging this failure
                    try:
                        pid = await card.get_attribute('data-profile-card-id') or f'unknown_{i+1}'
                        html = await card.inner_html()
                        path = f"rocketreach_card_{pid}.html"
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(html)
                        logger.info(f"Saved failing card HTML: {path}")
                    except Exception:
                        pass
                    continue
            
        except Exception as e:
            logger.error(f"Error extracting contacts from page {page_number}: {e}")
        
        return contacts
    
    async def _click_get_contact_info(self, card, position: int):
        """Click Get Contact Info button for a specific card"""
        try:
            # Get the profile ID from the card
            profile_id = await card.get_attribute('data-profile-card-id')
            logger.info(f"Clicking Get Contact Info for profile {profile_id} (position {position})")
            
            # First, try to click "View More" to expand the card
            view_more_buttons = await card.query_selector_all('button:has-text("View More")')
            if view_more_buttons:
                for button in view_more_buttons:
                    if await button.is_visible() and await button.is_enabled():
                        await button.click()
                        logger.info(f"Clicked View More button to expand card")
                        await self.page.wait_for_timeout(1000)  # Wait for expansion (reduced)
                        break
            
            # Look for Get Contact Info button within this card
            button_selectors = [
                'button:has-text("Get Contact Info")',
                'button:has-text("Get Contact")',
                'button:has-text("Get Contact Info ")',
                'button:has-text(" Get Contact Info")',
                '[data-testid="get-contact-button"]',
                '.get-contact-button',
                'button[class*="contact"]',
                'button[data-onboarding-id*="get-contact"]'
            ]
            
            button_clicked = False
            for selector in button_selectors:
                try:
                    # Look for button within this specific card
                    buttons = await card.query_selector_all(selector)
                    if buttons:
                        # Click the first visible and enabled button
                        for button in buttons:
                            if await button.is_visible() and await button.is_enabled():
                                await button.click()
                                logger.info(f"Clicked Get Contact Info button with selector: {selector}")
                                button_clicked = True
                                break
                        if button_clicked:
                            break
                except Exception as e:
                    logger.debug(f"Button selector {selector} failed: {e}")
                    continue
            
            if not button_clicked:
                # Try to fetch name to make the log more informative
                try:
                    name_el = await card.query_selector('#profile-name')
                    profile_name = (await name_el.inner_text()).strip() if name_el else ''
                except Exception:
                    profile_name = ''
                if profile_name:
                    logger.warning(f"❌ Could not find Get Contact Info button for profile {profile_id} - {profile_name}")
                else:
                    logger.warning(f"❌ Could not find Get Contact Info button for profile {profile_id}")
            
        except Exception as e:
            logger.warning(f"Error clicking Get Contact Info for position {position}: {e}")
    
    async def _extract_single_contact_after_click(self, card, page_number: int, position: int) -> Optional[Dict]:
        """Extract contact information after clicking Get Contact Info"""
        import re
        try:
            # Get fresh HTML content after clicking
            card_html = await card.inner_html()
            soup = BeautifulSoup(card_html, 'html.parser')
            
            # Extract basic information
            name_elem = soup.find('p', {'id': 'profile-name'})
            name = name_elem.get_text(strip=True) if name_elem else "N/A"
            
            title_elem = soup.find('p', class_='font-medium-420')
            title = title_elem.get_text(strip=True) if title_elem else "N/A"
            
            # Extract company
            company_elem = soup.find('a', href=lambda x: x and '-profile_' in x)
            company = "N/A"
            if company_elem:
                company_span = company_elem.find('span')
                if company_span:
                    company = company_span.get_text(strip=True)
            
            # Extract location
            location_elem = soup.find('span', class_='medium-420')
            location = location_elem.get_text(strip=True) if location_elem else "N/A"
            
            # Extract profile photo
            profile_photo = "N/A"
            img_elem = soup.find('img', {'id': 'profile-photo'})
            if img_elem and img_elem.get('src'):
                profile_photo = img_elem.get('src')
            
            # Extract social media links
            linkedin_url = "N/A"
            twitter_url = "N/A"
            social_buttons = soup.find_all('button', {'data-testid': 'social-button'})
            for button in social_buttons:
                title_attr = button.get('title', '').lower()
                if 'linkedin' in title_attr:
                    linkedin_url = "LinkedIn profile available"
                elif 'x' in title_attr or 'twitter' in title_attr:
                    twitter_url = "X/Twitter profile available"
            
            # Extract contact information - look for email after clicking
            contact_section = soup.find('div', {'data-onboarding-id': 'main-contact-info-section'})
            
            # Primary email - look for email patterns in text
            primary_email = "N/A"
            contact_grade = "N/A"
            if contact_section:
                # First try mailto links
                email_links = contact_section.find_all('a', href=lambda x: x and 'mailto:' in x)
                if email_links:
                    primary_email = email_links[0].get('href', '').replace('mailto:', '')
                else:
                    # Look for email patterns in text content
                    contact_text = contact_section.get_text()
                    import re
                    email_matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', contact_text)
                    if email_matches:
                        primary_email = email_matches[0]
                
                grade_elem = contact_section.find('span', {'data-testid': 'contact-grade-text'})
                if grade_elem:
                    contact_grade = grade_elem.get_text(strip=True)
            
            # Secondary email from "Other Contact Options"
            secondary_email = "N/A"
            other_contact_section = soup.find('div', {'data-onboarding-id': 'other-contact-info-section'})
            if other_contact_section:
                # First try mailto links
                other_email_links = other_contact_section.find_all('a', href=lambda x: x and 'mailto:' in x)
                if other_email_links:
                    secondary_email = other_email_links[0].get('href', '').replace('mailto:', '')
                else:
                    # Look for email patterns in text content
                    other_contact_text = other_contact_section.get_text()
                    import re
                    other_email_matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', other_contact_text)
                    if other_email_matches:
                        secondary_email = other_email_matches[0]
            
            # Extract work experience
            work_experience = []
            work_section = soup.find('li', class_='flex items-start gap-2 self-stretch')
            if work_section:
                briefcase_icon = work_section.find('i', class_='fa fa-briefcase fa-sm')
                if briefcase_icon:
                    work_list = work_section.find('ol', class_='flex flex-col')
                    if work_list:
                        work_items = work_list.find_all('li')
                        work_experience = [item.get_text(strip=True) for item in work_items]
            
            # Extract education
            education = []
            edu_sections = soup.find_all('li', class_='flex items-start gap-2 self-stretch')
            for edu_section in edu_sections:
                grad_icon = edu_section.find('i', class_='fa fa-graduation-cap fa-sm')
                if grad_icon:
                    edu_list = edu_section.find('ol', class_='flex flex-col')
                    if edu_list:
                        edu_items = edu_list.find_all('li')
                        education = [item.get_text(strip=True) for item in edu_items]
                    break
            
            # Extract skills
            skills = "N/A"
            skills_sections = soup.find_all('li', class_='flex items-start gap-2 self-stretch')
            for skills_section in skills_sections:
                book_icon = skills_section.find('i', class_='fa fa-book fa-sm')
                if book_icon:
                    skills_list = skills_section.find('ol')
                    if skills_list:
                        skills_item = skills_list.find('li')
                        if skills_item:
                            skills = skills_item.get_text(strip=True)
                    break
            
            # Extract phone
            phone = "N/A"
            if contact_section:
                phone_elem = contact_section.find('span', string=re.compile(r'\d{3}-\d{3}-'))
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
            
            # Determine best email to use
            best_email = primary_email if primary_email != "N/A" else secondary_email
            
            # Skip if no email
            if best_email == "N/A":
                logger.warning(f"No email found for contact {name} at position {position}")
                return None
            
            return {
                'name': name,
                'company': company,
                'title': title,
                'location': location,
                'email': best_email,
                'primary_email': primary_email,
                'secondary_email': secondary_email,
                'phone': phone,
                'profile_photo': profile_photo,
                'linkedin_url': linkedin_url,
                'twitter_url': twitter_url,
                'contact_grade': contact_grade,
                'work_experience': work_experience,
                'education': education,
                'skills': skills,
                'profile_id': await card.get_attribute('data-profile-card-id') or 'N/A',
                'page_number': page_number,
                'position_on_page': position,
                'raw_data': {
                    'profile_id': await card.get_attribute('data-profile-card-id') or 'N/A',
                    'extracted_from': 'rocketreach_web_crawler_after_click',
                    'contact_grade': contact_grade,
                    'work_experience_count': len(work_experience),
                    'education_count': len(education)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error extracting single contact after click: {e}")
            return None
    
    async def _extract_single_contact(self, card, page_number: int, position: int) -> Optional[Dict]:
        """Extract contact information from a single person card - logic từ crawl_rocketreach.py"""
        try:
            # Extract basic information
            name_elem = card.find('p', {'id': 'profile-name'})
            name = name_elem.get_text(strip=True) if name_elem else "N/A"
            
            title_elem = card.find('p', class_='font-medium-420')
            title = title_elem.get_text(strip=True) if title_elem else "N/A"
            
            # Extract company
            company_elem = card.find('a', href=lambda x: x and '-profile_' in x)
            company = "N/A"
            if company_elem:
                company_span = company_elem.find('span')
                if company_span:
                    company = company_span.get_text(strip=True)
            
            # Extract location
            location_elem = card.find('span', class_='medium-420')
            location = location_elem.get_text(strip=True) if location_elem else "N/A"
            
            # Extract profile photo
            profile_photo = "N/A"
            img_elem = card.find('img', {'id': 'profile-photo'})
            if img_elem and img_elem.get('src'):
                profile_photo = img_elem.get('src')
            
            # Extract social media links
            linkedin_url = "N/A"
            twitter_url = "N/A"
            social_buttons = card.find_all('button', {'data-testid': 'social-button'})
            for button in social_buttons:
                title_attr = button.get('title', '').lower()
                if 'linkedin' in title_attr:
                    linkedin_url = "LinkedIn profile available"
                elif 'x' in title_attr or 'twitter' in title_attr:
                    twitter_url = "X/Twitter profile available"
            
            # Extract contact information
            contact_section = card.find('div', {'data-onboarding-id': 'main-contact-info-section'})
            
            # Primary email
            primary_email = "N/A"
            contact_grade = "N/A"
            if contact_section:
                email_links = contact_section.find_all('a', href=lambda x: x and 'mailto:' in x)
                if email_links:
                    primary_email = email_links[0].get('href', '').replace('mailto:', '')
                
                grade_elem = contact_section.find('span', {'data-testid': 'contact-grade-text'})
                if grade_elem:
                    contact_grade = grade_elem.get_text(strip=True)
            
            # Secondary email from "Other Contact Options"
            secondary_email = "N/A"
            other_contact_section = card.find('div', {'data-onboarding-id': 'other-contact-info-section'})
            if other_contact_section:
                other_email_links = other_contact_section.find_all('a', href=lambda x: x and 'mailto:' in x)
                if other_email_links:
                    secondary_email = other_email_links[0].get('href', '').replace('mailto:', '')
            
            # Extract work experience
            work_experience = []
            work_section = card.find('li', class_='flex items-start gap-2 self-stretch')
            if work_section:
                briefcase_icon = work_section.find('i', class_='fa fa-briefcase fa-sm')
                if briefcase_icon:
                    work_list = work_section.find('ol', class_='flex flex-col')
                    if work_list:
                        work_items = work_list.find_all('li')
                        work_experience = [item.get_text(strip=True) for item in work_items]
            
            # Extract education
            education = []
            edu_sections = card.find_all('li', class_='flex items-start gap-2 self-stretch')
            for edu_section in edu_sections:
                grad_icon = edu_section.find('i', class_='fa fa-graduation-cap fa-sm')
                if grad_icon:
                    edu_list = edu_section.find('ol', class_='flex flex-col')
                    if edu_list:
                        edu_items = edu_list.find_all('li')
                        education = [item.get_text(strip=True) for item in edu_items]
                    break
            
            # Extract skills
            skills = "N/A"
            skills_sections = card.find_all('li', class_='flex items-start gap-2 self-stretch')
            for skills_section in skills_sections:
                book_icon = skills_section.find('i', class_='fa fa-book fa-sm')
                if book_icon:
                    skills_list = skills_section.find('ol')
                    if skills_list:
                        skills_item = skills_list.find('li')
                        if skills_item:
                            skills = skills_item.get_text(strip=True)
                    break
            
            # Extract phone
            phone = "N/A"
            if contact_section:
                phone_elem = contact_section.find('span', string=re.compile(r'\d{3}-\d{3}-'))
                if phone_elem:
                    phone = phone_elem.get_text(strip=True)
            
            # Determine best email to use
            best_email = primary_email if primary_email != "N/A" else secondary_email
            
            # Skip if no email
            if best_email == "N/A":
                return None
            
            return {
                'name': name,
                'company': company,
                'title': title,
                'location': location,
                'email': best_email,
                'primary_email': primary_email,
                'secondary_email': secondary_email,
                'phone': phone,
                'profile_photo': profile_photo,
                'linkedin_url': linkedin_url,
                'twitter_url': twitter_url,
                'contact_grade': contact_grade,
                'work_experience': work_experience,
                'education': education,
                'skills': skills,
                'profile_id': await card.get_attribute('data-profile-card-id') or 'N/A',
                'page_number': page_number,
                'position_on_page': position,
                'raw_data': {
                    'profile_id': await card.get_attribute('data-profile-card-id') or 'N/A',
                    'extracted_from': 'rocketreach_web_crawler',
                    'contact_grade': contact_grade,
                    'work_experience_count': len(work_experience),
                    'education_count': len(education)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error extracting single contact: {e}")
            return None
    
    async def save_contacts_to_db(self, contacts: List[Dict], source_url: str) -> int:
        """Save contacts to database and log counts (found/new/existing)."""
        saved_count = 0
        existing_count = 0
        
        for contact in contacts:
            try:
                # Check if contact already exists
                existing = await sync_to_async(RocketReachContact.objects.filter(email=contact['email']).first)()
                if existing:
                    logger.info(f"Contact {contact['email']} already exists, skipping")
                    existing_count += 1
                    continue
                
                # Create new contact
                # Normalize title category
                from apps.lawyers.models import RocketReachContact as RRCModel
                title_category = RRCModel.normalize_title_to_category(contact['title'])

                await sync_to_async(RocketReachContact.objects.create)(
                    email=contact['email'],
                    name=contact['name'],
                    company=contact['company'],
                    title=contact['title'],
                    title_category=title_category,
                    phone=contact['phone'],
                    location=contact['location'],
                    profile_photo=contact['profile_photo'],
                    linkedin_url=contact['linkedin_url'],
                    twitter_url=contact['twitter_url'],
                    primary_email=contact['primary_email'],
                    secondary_email=contact['secondary_email'],
                    contact_grade=contact['contact_grade'],
                    work_experience=contact['work_experience'],
                    education=contact['education'],
                    skills=contact['skills'],
                    profile_id=contact['profile_id'],
                    source_url=source_url,
                    page_number=contact['page_number'],
                    position_on_page=contact['position_on_page'],
                    confidence_score=0.8,
                    status='unknown',
                    raw_data=contact['raw_data']
                )
                
                saved_count += 1
                logger.info(f"Saved contact: {contact['name']} ({contact['email']})")
                
            except Exception as e:
                logger.error(f"Error saving contact {contact.get('email', 'unknown')}: {e}")
                continue
        
        total_found = len(contacts)
        logger.info(f"Save summary for {source_url}: found={total_found}, new={saved_count}, existing={existing_count}")
        return saved_count


# Async functions
async def crawl_rocketreach_web(base_url: str, headless: bool = True, max_pages: int = 10, page_size: int = 20, nav_timeout_sec: int = 60, start_page: int = 1) -> Dict:
    """Main function to crawl RocketReach web interface"""
    try:
        async with RocketReachWebCrawler(headless=headless, max_pages=max_pages, page_size=page_size, nav_timeout_sec=nav_timeout_sec, start_page=start_page) as crawler:
            # Login first
            login_success = await crawler.login()
            if not login_success:
                return {
                    'success': False,
                    'error': 'Login failed',
                    'contacts': []
                }
            
            # Crawl search results
            contacts = await crawler.crawl_search_results(base_url)
            
            # Save to database
            saved_count = await crawler.save_contacts_to_db(contacts, base_url)
            
            return {
                'success': True,
                'total_contacts': len(contacts),
                'saved_contacts': saved_count,
                'contacts': contacts,
                'source_url': base_url
            }
            
    except Exception as e:
        logger.error(f"Web crawling failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'contacts': []
        }


async def search_rocketreach_keyword(keyword: str, headless: bool = True) -> Dict:
    """Search RocketReach by keyword and get contact info"""
    try:
        async with RocketReachWebCrawler(headless=headless, max_pages=1) as crawler:
            # Login first
            login_success = await crawler.login()
            if not login_success:
                return {
                    'success': False,
                    'error': 'Login failed'
                }
            
            # Search and get contact
            result = await crawler.search_and_get_contact(keyword)
            return result
            
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Sync wrappers
def run_rocketreach_web_crawl(base_url: str, headless: bool = True, max_pages: int = 10, page_size: int = 20, nav_timeout_sec: int = 60, start_page: int = 1) -> Dict:
    """Synchronous wrapper for the async web crawler"""
    return asyncio.get_event_loop().run_until_complete(
        crawl_rocketreach_web(base_url, headless, max_pages, page_size, nav_timeout_sec, start_page)
    )


def run_rocketreach_keyword_search(keyword: str, headless: bool = True) -> Dict:
    """Synchronous wrapper for keyword search"""
    return asyncio.get_event_loop().run_until_complete(
        search_rocketreach_keyword(keyword, headless)
    )
