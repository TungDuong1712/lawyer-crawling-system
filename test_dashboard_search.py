#!/usr/bin/env python3
"""
Test script to test search functionality on RocketReach dashboard
"""
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dashboard_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
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
            
            # Submit form
            try:
                login_button = 'button[type="submit"]'
                await page.click(login_button)
                logger.info("Clicked login button")
            except Exception as e:
                logger.warning(f"Button click failed: {e}")
            
            # Wait for redirect to dashboard
            try:
                await page.wait_for_function(
                    "() => window.location.href.includes('/dashboard')",
                    timeout=15000
                )
                logger.info("Successfully logged in to dashboard")
            except Exception as e:
                logger.error(f"Failed to reach dashboard: {e}")
                return
            
            # Wait for dashboard to load
            await page.wait_for_timeout(5000)
            
            # Take screenshot of dashboard
            await page.screenshot(path='/tmp/dashboard_before_search.png', full_page=True)
            logger.info("Dashboard screenshot saved")
            
            # Test search functionality
            search_keyword = "jason shaw"
            logger.info(f"Testing search for: {search_keyword}")
            
            # Find search input
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[placeholder*="Search" i]',
                'input[name*="search" i]',
                'input[id*="search" i]',
                'input[class*="search" i]'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    search_input = selector
                    logger.info(f"Found search input with selector: {selector}")
                    break
                except:
                    continue
            
            if search_input:
                # Fill search input
                await page.fill(search_input, search_keyword)
                logger.info(f"Filled search input with: {search_keyword}")
                
                # Look for search button
                search_button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Search")',
                    'button:has-text("Find")',
                    'button[class*="search"]',
                    'input[type="submit"]'
                ]
                
                search_button = None
                for selector in search_button_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
                        search_button = selector
                        logger.info(f"Found search button with selector: {selector}")
                        break
                    except:
                        continue
                
                if search_button:
                    # Click search button
                    await page.click(search_button)
                    logger.info("Clicked search button")
                else:
                    # Try pressing Enter
                    await page.press(search_input, 'Enter')
                    logger.info("Pressed Enter in search input")
                
                # Wait for search results
                await page.wait_for_timeout(5000)
                
                # Take screenshot of search results
                await page.screenshot(path='/tmp/search_results.png', full_page=True)
                logger.info("Search results screenshot saved")
                
                # Check current URL
                current_url = page.url
                logger.info(f"Current URL after search: {current_url}")
                
                # Look for search results
                result_selectors = [
                    '.search-result',
                    '.result',
                    '.person-card',
                    '[data-testid="person-card"]',
                    '.contact-card',
                    '.profile-card'
                ]
                
                results_found = 0
                for selector in result_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            results_found = len(elements)
                            logger.info(f"Found {results_found} results with selector: {selector}")
                            break
                    except:
                        continue
                
                if results_found > 0:
                    logger.info(f"Search successful! Found {results_found} results")
                    
                    # Look for "Get Contact Info" buttons
                    contact_button_selectors = [
                        'button:has-text("Get Contact Info")',
                        'button:has-text("Get Contact")',
                        '[data-testid="get-contact-button"]',
                        '.get-contact-button',
                        'button[class*="contact"]'
                    ]
                    
                    contact_buttons = []
                    for selector in contact_button_selectors:
                        try:
                            buttons = await page.query_selector_all(selector)
                            if buttons:
                                contact_buttons = buttons
                                logger.info(f"Found {len(contact_buttons)} contact buttons with selector: {selector}")
                                break
                        except:
                            continue
                    
                    if contact_buttons:
                        logger.info("Found contact buttons - search functionality is working!")
                        
                        # Try to click first contact button
                        try:
                            await contact_buttons[0].click()
                            logger.info("Clicked first contact button")
                            
                            # Wait for contact info to load
                            await page.wait_for_timeout(3000)
                            
                            # Take screenshot of contact info
                            await page.screenshot(path='/tmp/contact_info.png', full_page=True)
                            logger.info("Contact info screenshot saved")
                            
                            # Look for email addresses
                            email_elements = await page.query_selector_all('text=/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/')
                            emails = []
                            for element in email_elements:
                                try:
                                    text = await element.inner_text()
                                    if text.strip() and '@' in text:
                                        emails.append(text.strip())
                                except:
                                    pass
                            
                            if emails:
                                logger.info(f"Found emails: {emails}")
                            else:
                                logger.info("No emails found in contact info")
                                
                        except Exception as e:
                            logger.warning(f"Failed to click contact button: {e}")
                    else:
                        logger.info("No contact buttons found")
                else:
                    logger.info("No search results found")
            else:
                logger.info("No search input found on dashboard")
            
        except Exception as e:
            logger.error(f"Error during dashboard search test: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard_search())
