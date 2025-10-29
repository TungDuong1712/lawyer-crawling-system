"""
Management command to run RocketReach web automation lookup.
"""

from django.core.management.base import BaseCommand, CommandError
from apps.lawyers.rocketreach_tasks import web_lookup_keyword_task
from apps.lawyers.rocketreach_web_crawler import run_rocketreach_keyword_search


class Command(BaseCommand):
    help = "Run RocketReach web lookup by keyword (uses Playwright)."

    def add_arguments(self, parser):
        parser.add_argument('keyword', type=str, help='Search keyword, e.g. "jayson shaw"')
        parser.add_argument('--headed', action='store_true', help='Run browser in headed mode for debugging')
        parser.add_argument('--async', action='store_true', help='Run as Celery task (default: sync)')
        parser.add_argument('--test-login', action='store_true', help='Test login only (no search)')
        parser.add_argument('--manual', action='store_true', help='Open browser for manual reCAPTCHA solving')

    def handle(self, *args, **options):
        keyword = options['keyword']
        headless = not options['headed']
        use_async = options['async']
        test_login = options['test_login']
        manual = options['manual']

        if test_login:
            self.stdout.write(self.style.NOTICE("Testing RocketReach login..."))
            try:
                from apps.lawyers.rocketreach_web_crawler import RocketReachWebCrawler
                import asyncio
                
                async def test_login():
                    async with RocketReachWebCrawler(headless=headless) as client:
                        return await client.login()
                
                result = asyncio.get_event_loop().run_until_complete(test_login())
                if result:
                    self.stdout.write(self.style.SUCCESS("Login test successful!"))
                else:
                    self.stdout.write(self.style.ERROR("Login test failed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Login test failed: {e}"))
            return

        if manual:
            self.stdout.write(self.style.NOTICE("Opening browser for manual reCAPTCHA solving..."))
            self.stdout.write(self.style.WARNING("Please solve the reCAPTCHA manually and the script will continue automatically."))
            try:
                result = run_rocketreach_keyword_search(keyword=keyword, headless=False)
                if result.get('success'):
                    emails = result.get('emails', [])
                    self.stdout.write(self.style.SUCCESS(f"Found {len(emails)} emails: {emails}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Manual lookup failed: {result.get('error', 'Unknown error')}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Manual lookup failed: {e}"))
            return

        if use_async:
            self.stdout.write(self.style.NOTICE(f"Enqueueing web lookup for keyword: {keyword}"))
            res = web_lookup_keyword_task.delay(keyword=keyword, headless=headless)
            self.stdout.write(self.style.SUCCESS(f"Queued Celery task: {res.id}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Running web lookup for keyword: {keyword}"))
            try:
                result = run_rocketreach_keyword_search(keyword=keyword, headless=headless)
                if result.get('success'):
                    emails = result.get('emails', [])
                    self.stdout.write(self.style.SUCCESS(f"Found {len(emails)} emails: {emails}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Lookup failed: {result.get('error', 'Unknown error')}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Lookup failed: {e}"))


