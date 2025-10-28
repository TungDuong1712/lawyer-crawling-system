#!/usr/bin/env python3
"""
Script to capture login interface and post-login dashboard
"""
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_login_interface():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Use headless mode for Docker
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
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to login page
            logger.info("Navigating to RocketReach login page...")
            await page.goto('https://rocketreach.co/login')
            await page.wait_for_load_state('networkidle')
            
            # Wait for Cloudflare protection
            try:
                await page.wait_for_function(
                    "() => !document.title.includes('Just a moment')",
                    timeout=30000
                )
                logger.info("Cloudflare protection passed")
            except:
                logger.warning("Cloudflare protection may still be active")
            
            # Wait for page to fully load
            await page.wait_for_timeout(5000)
            
            # Take screenshot of login page
            await page.screenshot(path='/tmp/login_page_interface.png', full_page=True)
            logger.info("Login page screenshot saved")
            
            # Fill login form
            email = 'santiago.wolfbrothers.ads@gmail.com'
            password = 'Hgiang2004@'
            
            # Find and fill email field
            email_input = 'input[type="email"]'
            await page.fill(email_input, email)
            logger.info("Filled email field")
            
            # Find and fill password field
            password_input = 'input[type="password"]'
            await page.fill(password_input, password)
            logger.info("Filled password field")
            
            # Take screenshot after filling form
            await page.screenshot(path='/tmp/login_form_filled.png', full_page=True)
            logger.info("Form filled screenshot saved")
            
            # Try to handle reCAPTCHA automatically
            logger.info("Attempting to handle reCAPTCHA automatically...")
            
            # Handle reCAPTCHA
            try:
                await page.evaluate("""
                    // Set recaptchaReady to true
                    window.recaptchaReady = true;
                    
                    // Try to simulate reCAPTCHA completion
                    if (typeof grecaptcha !== 'undefined') {
                        try {
                            const response = grecaptcha.getResponse();
                            if (response) {
                                console.log('reCAPTCHA response obtained:', response);
                                const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                                if (textarea) {
                                    textarea.value = response;
                                }
                            } else {
                                console.log('No reCAPTCHA response, simulating completion');
                                const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                                if (textarea) {
                                    textarea.value = 'fake_recaptcha_token_for_testing';
                                }
                                if (window.PLY_Service_RecaptchaV3Service_loaded) {
                                    window.PLY_Service_RecaptchaV3Service_loaded();
                                }
                            }
                        } catch(e) {
                            console.log('reCAPTCHA handling failed:', e);
                            window.recaptchaReady = true;
                            const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                            if (textarea) {
                                textarea.value = 'fake_recaptcha_token_for_testing';
                            }
                        }
                    } else {
                        console.log('grecaptcha not available, setting recaptchaReady manually');
                        window.recaptchaReady = true;
                        const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                        if (textarea) {
                            textarea.value = 'fake_recaptcha_token_for_testing';
                        }
                    }
                """)
                logger.info("reCAPTCHA handling completed")
            except Exception as e:
                logger.warning(f"reCAPTCHA handling failed: {e}")
            
            # Try to submit form
            try:
                login_button = 'button[type="submit"]'
                await page.click(login_button)
                logger.info("Clicked login button")
            except Exception as e:
                logger.warning(f"Button click failed: {e}")
            
            # Wait for redirect to dashboard or error
            try:
                await page.wait_for_function(
                    "() => window.location.href.includes('/dashboard') || window.location.href.includes('/login')",
                    timeout=15000  # 15 seconds timeout
                )
                
                current_url = page.url
                logger.info(f"Current URL after login attempt: {current_url}")
                
                if '/dashboard' in current_url:
                    logger.info("Login successful! Capturing dashboard...")
                    
                    # Wait for dashboard to load
                    await page.wait_for_timeout(5000)
                    
                    # Take screenshot of dashboard
                    await page.screenshot(path='/tmp/dashboard_interface.png', full_page=True)
                    logger.info("Dashboard screenshot saved")
                    
                    # Get page title
                    title = await page.title()
                    logger.info(f"Dashboard title: {title}")
                    
                    # Check for search functionality
                    search_elements = await page.query_selector_all('input[type="search"], input[placeholder*="search" i], input[placeholder*="Search" i]')
                    logger.info(f"Found {len(search_elements)} search elements")
                    
                    # Check for navigation menu
                    nav_elements = await page.query_selector_all('nav, .navbar, .navigation, .menu')
                    logger.info(f"Found {len(nav_elements)} navigation elements")
                    
                    # Check for user profile/account elements
                    profile_elements = await page.query_selector_all('[class*="profile"], [class*="user"], [class*="account"]')
                    logger.info(f"Found {len(profile_elements)} profile elements")
                    
                else:
                    logger.warning("Login failed or redirected back to login page")
                    
                    # Take screenshot of error state
                    await page.screenshot(path='/tmp/login_error_state.png', full_page=True)
                    logger.info("Login error state screenshot saved")
                    
                    # Check for error messages
                    error_elements = await page.query_selector_all('.error, [class*="error"], .alert-danger, .invalid-feedback')
                    if error_elements:
                        for i, element in enumerate(error_elements):
                            try:
                                text = await element.inner_text()
                                if text.strip():
                                    logger.info(f"Error message {i}: {text.strip()}")
                            except:
                                pass
                
            except Exception as e:
                logger.error(f"Error waiting for login completion: {e}")
                
                # Take screenshot of current state
                await page.screenshot(path='/tmp/login_timeout_state.png', full_page=True)
                logger.info("Login timeout state screenshot saved")
            
            # Wait a bit more for interface to load
            logger.info("Waiting 5 seconds for interface to load...")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            logger.error(f"Error during interface capture: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_login_interface())
