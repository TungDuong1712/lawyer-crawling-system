#!/usr/bin/env python3
"""
Test script to investigate AngularJS form handling on RocketReach
"""
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_angular_form():
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
            
            # Find form elements
            email_input = 'input[type="email"]'
            password_input = 'input[type="password"]'
            login_button = 'button[type="submit"]'
            
            # Fill form using different methods
            email = 'santiago.wolfbrothers.ads@gmail.com'
            password = 'Hgiang2004@'
            
            logger.info("Testing different form filling methods...")
            
            # Method 1: Direct value setting
            await page.evaluate(f"""
                const emailField = document.querySelector('{email_input}');
                const passwordField = document.querySelector('{password_input}');
                
                if (emailField && passwordField) {{
                    // Set values directly
                    emailField.value = '{email}';
                    passwordField.value = '{password}';
                    
                    // Trigger events
                    emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    console.log('Method 1: Direct value setting completed');
                }}
            """)
            
            await page.wait_for_timeout(2000)
            
            # Check if values are still there
            email_value = await page.evaluate(f"document.querySelector('{email_input}').value")
            password_value = await page.evaluate(f"document.querySelector('{password_input}').value")
            
            logger.info(f"After Method 1 - Email: {email_value}, Password: {password_value}")
            
            # Method 2: AngularJS scope binding
            await page.evaluate(f"""
                const emailField = document.querySelector('{email_input}');
                const passwordField = document.querySelector('{password_input}');
                
                if (emailField && passwordField) {{
                    // Try to find AngularJS scope
                    const emailScope = angular.element(emailField).scope();
                    const passwordScope = angular.element(passwordField).scope();
                    
                    if (emailScope) {{
                        // Set scope values
                        emailScope.$apply(function() {{
                            emailScope.signupForm = emailScope.signupForm || {{}};
                            emailScope.signupForm.email = emailScope.signupForm.email || {{}};
                            emailScope.signupForm.email.value = '{email}';
                        }});
                        console.log('AngularJS email scope set');
                    }}
                    
                    if (passwordScope) {{
                        passwordScope.$apply(function() {{
                            passwordScope.signupForm = passwordScope.signupForm || {{}};
                            passwordScope.signupForm.password = passwordScope.signupForm.password || {{}};
                            passwordScope.signupForm.password.value = '{password}';
                        }});
                        console.log('AngularJS password scope set');
                    }}
                    
                    // Also set DOM values
                    emailField.value = '{email}';
                    passwordField.value = '{password}';
                    
                    // Trigger events
                    emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    console.log('Method 2: AngularJS scope binding completed');
                }}
            """)
            
            await page.wait_for_timeout(2000)
            
            # Check values again
            email_value = await page.evaluate(f"document.querySelector('{email_input}').value")
            password_value = await page.evaluate(f"document.querySelector('{password_input}').value")
            
            logger.info(f"After Method 2 - Email: {email_value}, Password: {password_value}")
            
            # Method 3: Try to find ng-model attributes
            ng_models = await page.evaluate("""
                const inputs = document.querySelectorAll('input[ng-model]');
                const models = [];
                inputs.forEach(input => {
                    models.push({
                        element: input.tagName,
                        ngModel: input.getAttribute('ng-model'),
                        value: input.value
                    });
                });
                return models;
            """)
            
            logger.info(f"Found ng-model attributes: {ng_models}")
            
            # Method 4: Try to set values using ng-model
            if ng_models:
                await page.evaluate(f"""
                    const emailField = document.querySelector('{email_input}');
                    const passwordField = document.querySelector('{password_input}');
                    
                    if (emailField && passwordField) {{
                        // Try to find the controller
                        const form = document.querySelector('form');
                        if (form) {{
                            const controller = angular.element(form).controller('ngForm');
                            
                            if (controller) {{
                                // Set form values
                                controller.signupForm = controller.signupForm || {{}};
                                controller.signupForm.email = controller.signupForm.email || {{}};
                                controller.signupForm.password = controller.signupForm.password || {{}};
                                
                                controller.signupForm.email.value = '{email}';
                                controller.signupForm.password.value = '{password}';
                                
                                // Update DOM
                                emailField.value = '{email}';
                                passwordField.value = '{password}';
                                
                                // Trigger digest cycle
                                controller.$apply();
                                
                                console.log('Method 4: ng-model controller binding completed');
                            }}
                        }}
                    }}
                """)
            
            await page.wait_for_timeout(2000)
            
            # Final check
            email_value = await page.evaluate(f"document.querySelector('{email_input}').value")
            password_value = await page.evaluate(f"document.querySelector('{password_input}').value")
            
            logger.info(f"Final values - Email: {email_value}, Password: {password_value}")
            
            # Take screenshot
            await page.screenshot(path='/tmp/angular_form_test.png')
            logger.info('Screenshot saved to /tmp/angular_form_test.png')
            
        except Exception as e:
            logger.error(f"Error during testing: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_angular_form())
