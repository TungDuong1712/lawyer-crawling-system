#!/usr/bin/env python3
"""
Debug script to inspect RocketReach login page and find reCAPTCHA elements
"""
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_recaptcha():
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
            
            # Take initial screenshot
            await page.screenshot(path='/tmp/debug_initial_page.png')
            logger.info("Initial page screenshot saved")
            
            # Look for all possible reCAPTCHA indicators
            recaptcha_selectors = [
                '.g-recaptcha',
                'iframe[src*="recaptcha"]',
                'iframe[title*="reCAPTCHA"]',
                'iframe[title*="recaptcha"]',
                '[class*="recaptcha"]',
                '[id*="recaptcha"]',
                'div[data-sitekey]',
                '.recaptcha-checkbox',
                '#recaptcha',
                'iframe[src*="google.com/recaptcha"]',
                'iframe[src*="gstatic.com"]',
                '[data-callback]',
                '[data-expired-callback]',
                '[data-error-callback]'
            ]
            
            logger.info("Searching for reCAPTCHA elements...")
            found_elements = {}
            
            for selector in recaptcha_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        found_elements[selector] = len(elements)
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        # Get element details
                        for i, element in enumerate(elements):
                            try:
                                tag_name = await element.evaluate('el => el.tagName')
                                class_name = await element.get_attribute('class') or 'N/A'
                                id_name = await element.get_attribute('id') or 'N/A'
                                src = await element.get_attribute('src') or 'N/A'
                                
                                logger.info(f"  Element {i}: {tag_name}, class='{class_name}', id='{id_name}', src='{src}'")
                                
                                # Screenshot this specific element
                                await element.screenshot(path=f'/tmp/debug_element_{selector.replace("[", "_").replace("]", "_").replace("*", "_")}_{i}.png')
                                
                            except Exception as e:
                                logger.warning(f"Could not inspect element {i}: {e}")
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
            
            if not found_elements:
                logger.info("No reCAPTCHA elements found with standard selectors")
                
                # Look for any iframes
                logger.info("Looking for any iframes...")
                iframes = await page.query_selector_all('iframe')
                logger.info(f"Found {len(iframes)} iframes total")
                
                for i, iframe in enumerate(iframes):
                    try:
                        src = await iframe.get_attribute('src') or 'N/A'
                        title = await iframe.get_attribute('title') or 'N/A'
                        logger.info(f"  Iframe {i}: src='{src}', title='{title}'")
                        
                        if 'recaptcha' in src.lower() or 'recaptcha' in title.lower():
                            await iframe.screenshot(path=f'/tmp/debug_iframe_{i}_recaptcha.png')
                            logger.info(f"  Screenshot saved for iframe {i}")
                    except Exception as e:
                        logger.warning(f"Could not inspect iframe {i}: {e}")
            
            # Take full page screenshot
            await page.screenshot(path='/tmp/debug_full_page.png', full_page=True)
            logger.info("Full page screenshot saved")
            
            # Get page source for analysis
            content = await page.content()
            with open('/tmp/debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("Page source saved to /tmp/debug_page_source.html")
            
            # Look for reCAPTCHA in page source
            if 'recaptcha' in content.lower():
                logger.info("Found 'recaptcha' in page source")
            else:
                logger.info("No 'recaptcha' found in page source")
            
            # Check for Google reCAPTCHA scripts
            scripts = await page.query_selector_all('script[src*="recaptcha"]')
            if scripts:
                logger.info(f"Found {len(scripts)} reCAPTCHA scripts")
                for i, script in enumerate(scripts):
                    src = await script.get_attribute('src') or 'N/A'
                    logger.info(f"  Script {i}: {src}")
            else:
                logger.info("No reCAPTCHA scripts found")
            
            # Wait a bit more for any dynamic content
            logger.info("Waiting 5 seconds for dynamic content...")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            logger.error(f"Error during debugging: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_recaptcha())
