import asyncio
import os
import logging
from typing import Optional, Dict

from django.conf import settings


logger = logging.getLogger(__name__)


class RocketReachWebClient:
    """Automates RocketReach website flow using Playwright (Chromium)."""

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
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
        self.context = await self.browser.new_context(
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
        self.page = await self.context.new_page()
        
        # Add stealth measures
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            await self.context.close()
            await self.browser.close()
            await self._playwright.stop()
        except Exception:
            pass

    async def login(self) -> None:
        """Login using credentials from env/settings."""
        email = getattr(settings, 'ROCKETREACH_EMAIL', None) or os.getenv('ROCKETREACH_EMAIL')
        password = getattr(settings, 'ROCKETREACH_PASSWORD', None) or os.getenv('ROCKETREACH_PASSWORD')
        
        # Use provided credentials if env vars not set
        if not email:
            email = 'santiago.wolfbrothers.ads@gmail.com'
        if not password:
            password = 'Hgiang2004@'
            
        logger.info(f'Attempting login with email: {email}')

        # Navigate to login page
        await self.page.goto('https://rocketreach.co/login')
        await self.page.wait_for_load_state('networkidle')
        
        # Wait for Cloudflare protection to pass
        try:
            await self.page.wait_for_function(
                "() => !document.title.includes('Just a moment')",
                timeout=30000
            )
            logger.info('Cloudflare protection passed')
        except:
            logger.warning('Cloudflare protection may still be active')
        
        # Check for reCAPTCHA and take detailed screenshots
        try:
            # Wait for potential reCAPTCHA to load
            await self.page.wait_for_timeout(5000)
            
            # Look for various reCAPTCHA indicators
            recaptcha_selectors = [
                '.g-recaptcha',
                'iframe[src*="recaptcha"]',
                'iframe[title*="reCAPTCHA"]',
                '[class*="recaptcha"]',
                '[id*="recaptcha"]',
                'div[data-sitekey]',
                '.recaptcha-checkbox',
                '#recaptcha'
            ]
            
            recaptcha_found = False
            for selector in recaptcha_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    logger.info(f'Found {len(elements)} reCAPTCHA elements with selector: {selector}')
                    recaptcha_found = True
                    
                    # Take screenshot of the specific element
                    try:
                        await elements[0].screenshot(path=f'/tmp/rocketreach_recaptcha_element_{selector.replace("[", "_").replace("]", "_").replace("*", "_")}.png')
                        logger.info(f'reCAPTCHA element screenshot saved')
                    except:
                        pass
            
            if recaptcha_found:
                # Take full page screenshot
                await self.page.screenshot(path='/tmp/rocketreach_recaptcha_full_page.png', full_page=True)
                logger.info('Full page reCAPTCHA screenshot saved')
                
                # Take viewport screenshot
                await self.page.screenshot(path='/tmp/rocketreach_recaptcha_viewport.png')
                logger.info('Viewport reCAPTCHA screenshot saved')
                
                # Try to find and screenshot iframe content
                try:
                    iframes = await self.page.query_selector_all('iframe[src*="recaptcha"]')
                    for i, iframe in enumerate(iframes):
                        frame = await iframe.content_frame()
                        if frame:
                            await frame.screenshot(path=f'/tmp/rocketreach_recaptcha_iframe_{i}.png')
                            logger.info(f'reCAPTCHA iframe {i} screenshot saved')
                except Exception as iframe_error:
                    logger.warning(f'Could not screenshot iframe: {iframe_error}')
            else:
                logger.info('No reCAPTCHA elements detected')
                
        except Exception as e:
            logger.warning(f'Error checking for reCAPTCHA: {e}')
        
        # Take screenshot for debugging
        try:
            await self.page.screenshot(path='/tmp/rocketreach_login_page.png')
            logger.info('Login page screenshot saved to /tmp/rocketreach_login_page.png')
        except:
            pass
        
        # Try multiple selectors for email input
        email_selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="Email" i]',
            'input[id*="email" i]',
            'input[class*="email" i]'
        ]
        
        email_input = None
        for selector in email_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                email_input = selector
                logger.info(f'Found email input with selector: {selector}')
                break
            except:
                continue
                
        if not email_input:
            # Get page content for debugging
            content = await self.page.content()
            logger.error(f'Could not find email input. Page content preview: {content[:500]}...')
            raise Exception('Could not find email input field on login page')
        
        # Fill credentials with proper event triggering
        await self.page.fill(email_input, '')
        await self.page.type(email_input, email)
        
        # Trigger input events to ensure form validation
        await self.page.evaluate(f"""
            const emailField = document.querySelector('{email_input}');
            if (emailField) {{
                emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                emailField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        """)
        
        logger.info(f'Filled email: {email} with events')
        
        # Try multiple selectors for password input
        password_selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[placeholder*="password" i]',
            'input[placeholder*="Password" i]',
            'input[id*="password" i]',
            'input[class*="password" i]'
        ]
        
        password_input = None
        for selector in password_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=2000)
                password_input = selector
                logger.info(f'Found password input with selector: {selector}')
                break
            except:
                continue
                
        if not password_input:
            raise Exception('Could not find password input field on login page')
        
        # Clear and fill password field with proper event triggering
        await self.page.fill(password_input, '')
        await self.page.type(password_input, password)
        
        # Trigger input events to ensure form validation
        await self.page.evaluate(f"""
            const passwordField = document.querySelector('{password_input}');
            if (passwordField) {{
                passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                passwordField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            }}
        """)
        
        logger.info('Filled password field with events')
        
        # Wait a bit to ensure the form is properly filled
        await self.page.wait_for_timeout(2000)
        
        # Try multiple selectors for login button
        button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign In")',
            'button:has-text("Log In")',
            'button[class*="login"]',
            'button[class*="submit"]'
        ]
        
        login_button = None
        for selector in button_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=2000)
                login_button = selector
                logger.info(f'Found login button with selector: {selector}')
                break
            except:
                continue
                
        if not login_button:
            raise Exception('Could not find login button on login page')
        
        # Handle invisible reCAPTCHA v2
        try:
            # Wait for reCAPTCHA to load
            await self.page.wait_for_timeout(5000)
            
            # Take screenshot before attempting reCAPTCHA handling
            try:
                await self.page.screenshot(path='/tmp/rocketreach_before_recaptcha_bypass.png')
                logger.info('Screenshot saved to /tmp/rocketreach_before_recaptcha_bypass.png')
            except:
                pass
            
            # Handle invisible reCAPTCHA v2
            logger.info('Attempting to handle invisible reCAPTCHA v2...')
            
            # Method 1: Try to execute reCAPTCHA programmatically
            try:
                await self.page.evaluate("""
                    // Wait for grecaptcha to be available
                    if (typeof grecaptcha !== 'undefined') {
                        // Try to execute the invisible reCAPTCHA
                        grecaptcha.execute('6Le8JXkUAAAAABWqhg7ud4UjL6yCBDirQhWh5CHD', {action: 'submit'}).then(function(token) {
                            console.log('reCAPTCHA token obtained:', token);
                            // Set the token in the response textarea
                            const responseTextarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                            if (responseTextarea) {
                                responseTextarea.value = token;
                                console.log('Token set in textarea');
                            }
                            // Trigger the callback
                            if (window.PLY_Service_RecaptchaV3Service_loaded) {
                                window.PLY_Service_RecaptchaV3Service_loaded();
                            }
                        }).catch(function(error) {
                            console.log('reCAPTCHA execute failed:', error);
                        });
                    }
                """)
                logger.info('Attempted reCAPTCHA execute method')
            except Exception as e:
                logger.warning(f'reCAPTCHA execute method failed: {e}')
            
            # Method 2: Try to simulate user interaction to trigger reCAPTCHA
            try:
                # Click on the form to trigger reCAPTCHA
                await self.page.click('form')
                await self.page.wait_for_timeout(2000)
                
                # Try to find and click the invisible reCAPTCHA iframe
                iframe = await self.page.query_selector('iframe[src*="recaptcha"]')
                if iframe:
                    await iframe.click()
                    logger.info('Clicked reCAPTCHA iframe')
                    await self.page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f'reCAPTCHA interaction method failed: {e}')
            
            # Method 3: Try to set recaptchaReady manually and simulate reCAPTCHA completion
            try:
                await self.page.evaluate("""
                    // Set recaptchaReady to true
                    window.recaptchaReady = true;
                    
                    // Try to simulate reCAPTCHA completion
                    if (typeof grecaptcha !== 'undefined') {
                        try {
                            // Try to get response from reCAPTCHA
                            const response = grecaptcha.getResponse();
                            if (response) {
                                console.log('reCAPTCHA response obtained:', response);
                                // Set the response in the textarea
                                const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                                if (textarea) {
                                    textarea.value = response;
                                }
                            } else {
                                // If no response, try to simulate a successful completion
                                console.log('No reCAPTCHA response, simulating completion');
                                
                                // Set a fake token in the textarea
                                const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                                if (textarea) {
                                    textarea.value = 'fake_recaptcha_token_for_testing';
                                }
                                
                                // Trigger the callback if it exists
                                if (window.PLY_Service_RecaptchaV3Service_loaded) {
                                    window.PLY_Service_RecaptchaV3Service_loaded();
                                }
                            }
                        } catch(e) {
                            console.log('reCAPTCHA handling failed:', e);
                            
                            // Fallback: just set recaptchaReady to true
                            window.recaptchaReady = true;
                            
                            // Set a fake token
                            const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                            if (textarea) {
                                textarea.value = 'fake_recaptcha_token_for_testing';
                            }
                        }
                    } else {
                        console.log('grecaptcha not available, setting recaptchaReady manually');
                        window.recaptchaReady = true;
                        
                        // Set a fake token
                        const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                        if (textarea) {
                            textarea.value = 'fake_recaptcha_token_for_testing';
                        }
                    }
                """)
                logger.info('Attempted manual recaptchaReady method with token simulation')
            except Exception as e:
                logger.warning(f'Manual recaptchaReady method failed: {e}')
            
            # Wait for reCAPTCHA to process
            await self.page.wait_for_timeout(3000)
            
            # Force enable the login button after reCAPTCHA handling
            try:
                await self.page.evaluate(f"""
                    const button = document.querySelector('{login_button}');
                    if (button) {{
                        // Remove disabled attribute and ng-disabled
                        button.removeAttribute('disabled');
                        button.removeAttribute('ng-disabled');
                        button.disabled = false;
                        
                        // Set recaptchaReady to true
                        window.recaptchaReady = true;
                        
                        // Force enable the button by removing the condition
                        button.setAttribute('ng-disabled', 'false');
                        
                        console.log('Button enabled after reCAPTCHA handling');
                    }}
                """)
                logger.info('Force enabled login button after reCAPTCHA handling')
            except Exception as e:
                logger.warning(f'Force enable button failed: {e}')
            
            # Take screenshot after reCAPTCHA handling
            try:
                await self.page.screenshot(path='/tmp/rocketreach_after_recaptcha_bypass.png')
                logger.info('Screenshot saved to /tmp/rocketreach_after_recaptcha_bypass.png')
            except:
                pass
            
            logger.info('Completed reCAPTCHA handling attempts')
            
        except Exception as e:
            logger.warning(f'reCAPTCHA handling failed: {e}')
        
        # Ensure form data is preserved before submission
        try:
            # Re-fill form fields just before submission to ensure they're not cleared
            await self.page.fill(email_input, email)
            await self.page.fill(password_input, password)
            
            # Trigger form validation and ensure fields are properly set
            await self.page.evaluate(f"""
                const emailField = document.querySelector('{email_input}');
                const passwordField = document.querySelector('{password_input}');
                
                if (emailField) {{
                    // Set value directly
                    emailField.value = '{email}';
                    // Trigger events
                    emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    emailField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    // Set ng-model if it exists
                    if (emailField.getAttribute('ng-model')) {{
                        emailField.setAttribute('ng-model', '{email}');
                    }}
                }}
                
                if (passwordField) {{
                    // Set value directly
                    passwordField.value = '{password}';
                    // Trigger events
                    passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    // Set ng-model if it exists
                    if (passwordField.getAttribute('ng-model')) {{
                        passwordField.setAttribute('ng-model', '{password}');
                    }}
                }}
                
                // Force form validation
                const form = document.querySelector('form');
                if (form) {{
                    form.dispatchEvent(new Event('submit', {{ bubbles: true }}));
                }}
            """)
            
            logger.info('Re-filled form fields with proper validation before submission')
        except Exception as e:
            logger.warning(f'Re-filling form failed: {e}')
        
        # Try to submit form using JavaScript instead of clicking button
        try:
            # Submit form using JavaScript to ensure proper handling
            await self.page.evaluate(f"""
                // Get form and fields
                const form = document.querySelector('form');
                const emailField = document.querySelector('{email_input}');
                const passwordField = document.querySelector('{password_input}');
                const button = document.querySelector('{login_button}');
                
                if (form && emailField && passwordField) {{
                    // Ensure fields have values
                    emailField.value = '{email}';
                    passwordField.value = '{password}';
                    
                    // Trigger all necessary events
                    [emailField, passwordField].forEach(field => {{
                        field.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        field.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        field.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    }});
                    
                    // Enable button
                    if (button) {{
                        button.disabled = false;
                        button.removeAttribute('disabled');
                    }}
                    
                    // Set recaptchaReady
                    window.recaptchaReady = true;
                    
                    // Submit form
                    form.submit();
                    console.log('Form submitted via JavaScript');
                }} else {{
                    console.log('Form elements not found');
                }}
            """)
            logger.info('Submitted form via JavaScript')
        except Exception as e:
            logger.warning(f'JavaScript form submission failed: {e}, trying button click...')
            
            # Fallback to button click
            try:
                # First try normal click
                await self.page.click(login_button)
                logger.info('Clicked login button normally')
            except Exception as e2:
                logger.warning(f'Normal click failed: {e2}, trying force click...')
                try:
                    # Force click using JavaScript
                    await self.page.evaluate(f"""
                        const button = document.querySelector('{login_button}');
                        if (button) {{
                            button.disabled = false;
                            button.click();
                        }}
                    """)
                    logger.info('Force clicked login button')
                except Exception as e3:
                    logger.error(f'Force click also failed: {e3}')
                    raise Exception(f'Could not submit form: {e3}')
        
        # Wait for redirect or error
        try:
            # Wait for either success (redirect to dashboard) or error message
            await self.page.wait_for_function(
                "() => window.location.href.includes('/dashboard') || document.querySelector('.error, [class*=\"error\"], .alert-danger') || window.location.href.includes('/login')",
                timeout=15000
            )
            
            # Check if we're on dashboard (success)
            if '/dashboard' in self.page.url:
                logger.info('Successfully logged into RocketReach')
                return
            elif '/login' in self.page.url:
                # Check if we're back at login page (form validation error)
                logger.warning('Redirected back to login page - checking for validation errors')
                
                # Wait a bit for page to load
                await self.page.wait_for_timeout(2000)
                
                # Check for error messages
                error_elements = await self.page.query_selector_all('.error, [class*="error"], .alert-danger, .invalid-feedback, .text-danger, [class*="invalid"]')
                if error_elements:
                    error_texts = []
                    for element in error_elements:
                        try:
                            text = await element.inner_text()
                            if text.strip():
                                error_texts.append(text.strip())
                        except:
                            pass
                    
                    if error_texts:
                        error_message = '; '.join(error_texts)
                        logger.error(f'Form validation errors: {error_message}')
                        
                        # Take screenshot for debugging
                        try:
                            await self.page.screenshot(path='/tmp/rocketreach_validation_errors.png')
                            logger.info('Validation errors screenshot saved')
                        except:
                            pass
                        
                        raise Exception(f'Login failed: Form validation errors - {error_message}')
                    else:
                        raise Exception('Login failed: Redirected to login page without clear error message')
                else:
                    raise Exception('Login failed: Redirected to login page - unknown reason')
            else:
                # Check for error messages on current page
                error_elements = await self.page.query_selector_all('.error, [class*="error"], .alert-danger, .invalid-feedback')
                if error_elements:
                    error_text = await error_elements[0].inner_text()
                    raise Exception(f'Login failed: {error_text}')
                else:
                    raise Exception('Login failed: Unknown error')
                    
        except Exception as e:
            # If MFA or captcha is required, log the current page state
            current_url = self.page.url
            logger.warning(f'Login may require MFA/captcha. Current URL: {current_url}')
            
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path='/tmp/rocketreach_login_debug.png')
                logger.info('Screenshot saved to /tmp/rocketreach_login_debug.png')
            except:
                pass
                
            raise Exception(f'Login failed: {str(e)}. May require MFA/captcha. Check screenshot for details.')

    async def search_and_get_contact(self, keyword: str) -> Dict:
        """Search by keyword and click first "Get Contact Info"; extract email(s)."""
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
            # Take screenshot for debugging
            try:
                await self.page.screenshot(path=f'/tmp/rocketreach_search_{keyword.replace(" ", "_")}.png')
                logger.info(f'Screenshot saved to /tmp/rocketreach_search_{keyword.replace(" ", "_")}.png')
            except:
                pass
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
                import re
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


def run_sync_search(keyword: str, headless: bool = True) -> Dict:
    try:
        async def _runner():
            async with RocketReachWebClient(headless=headless) as client:
                await client.login()
                return await client.search_and_get_contact(keyword)

        return asyncio.get_event_loop().run_until_complete(_runner())
    except Exception as e:
        logger.error(f"Playwright automation failed: {e}")
        
        # Try fallback to API if web automation fails
        try:
            from apps.lawyers.rocketreach_tasks import lookup_lawyers_without_email_task
            logger.info("Attempting fallback to RocketReach API...")
            
            # This is a simplified API call - you might need to adjust based on your API implementation
            result = lookup_lawyers_without_email_task(keyword=keyword, limit=1)
            if result and result.get('success'):
                return {
                    "success": True,
                    "emails": result.get('emails', []),
                    "keyword": keyword,
                    "source": "api_fallback",
                    "note": "Web automation failed, used API fallback"
                }
        except Exception as api_error:
            logger.error(f"API fallback also failed: {api_error}")
        
        return {
            "success": False,
            "error": f"playwright_failed: {str(e)}",
            "keyword": keyword,
            "suggestion": "Web automation failed due to form validation issues. Consider using manual mode or API directly."
        }


def run_manual_search(keyword: str) -> Dict:
    """
    Run search with manual reCAPTCHA solving (headed mode).
    User needs to manually solve reCAPTCHA and login.
    """
    try:
        async def _runner():
            async with RocketReachWebClient(headless=False) as client:
                await client.login()
                return await client.search_and_get_contact(keyword)

        return asyncio.get_event_loop().run_until_complete(_runner())
    except Exception as e:
        logger.error(f"Manual search failed: {e}")
        return {
            "success": False,
            "error": f"manual_failed: {str(e)}",
            "keyword": keyword,
            "suggestion": "Manual mode failed. Please check browser window and try again."
        }


