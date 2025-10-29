"""
RocketReach Management Commands
Tất cả commands cho RocketReach: web crawl, keyword search, sample data
"""

import asyncio
import logging
import re
from pathlib import Path
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from asgiref.sync import sync_to_async

from apps.lawyers.models import RocketReachContact
from apps.lawyers.rocketreach_web_crawler import run_rocketreach_web_crawl, run_rocketreach_keyword_search

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'RocketReach crawling commands - tất cả flow Playwright'

    def add_arguments(self, parser):
        # Subcommands
        subparsers = parser.add_subparsers(dest='method', help='Crawling method')
        
        # Web crawling với pagination
        web_parser = subparsers.add_parser('crawl', help='Crawl RocketReach với pagination')
        web_parser.add_argument('--url', type=str, required=True, help='RocketReach search URL')
        web_parser.add_argument('--start-page', type=int, default=1, help='Starting page (default: 1)')
        web_parser.add_argument('--num-pages', type=int, default=3, help='Number of pages (default: 3)')
        web_parser.add_argument('--page-size', type=int, default=20, help='Page size (default: 20)')
        web_parser.add_argument('--headless', action='store_true', help='Run in headless mode')
        web_parser.add_argument('--timeout', type=int, default=30, help='Timeout per page (seconds)')
        web_parser.add_argument('--debug-analyze-snapshots', action='store_true', help='After crawl, analyze saved snapshots (emails/cards) and print summary')
        
        # Keyword search
        search_parser = subparsers.add_parser('search', help='Search by keyword và get contact info')
        search_parser.add_argument('--keyword', type=str, required=True, help='Search keyword')
        search_parser.add_argument('--headless', action='store_true', help='Run in headless mode')
        
        # Sample data
        sample_parser = subparsers.add_parser('sample', help='Create sample contacts for testing')
        sample_parser.add_argument('--url', type=str, required=True, help='Base URL for sample data')
        sample_parser.add_argument('--start-page', type=int, default=1, help='Starting page (default: 1)')
        sample_parser.add_argument('--num-pages', type=int, default=3, help='Number of pages (default: 3)')
        sample_parser.add_argument('--page-size', type=int, default=20, help='Page size (default: 20)')

    def handle(self, *args, **options):
        method = options.get('method')
        
        if not method:
            self.stdout.write(self.style.ERROR('Please specify a method: crawl, search, or sample'))
            return
        
        if method == 'crawl':
            self.handle_web_crawl(options)
        elif method == 'search':
            self.handle_keyword_search(options)
        elif method == 'sample':
            self.handle_sample_data(options)
        else:
            self.stdout.write(self.style.ERROR(f'Unknown method: {method}'))

    def handle_web_crawl(self, options):
        """Handle web crawling with pagination"""
        url = options['url']
        start_page = options['start_page']
        num_pages = options['num_pages']
        page_size = options['page_size']
        headless = options['headless']
        timeout = options['timeout']
        debug_analyze = options.get('debug_analyze_snapshots', False)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting web crawl: {url}, pages {start_page}-{start_page + num_pages - 1}, size {page_size}, timeout {timeout}s'
            )
        )
        
        try:
            # Build URL with pagination
            if 'start=1' in url:
                start = (start_page - 1) * page_size + 1
                url = url.replace('start=1', f'start={start}')
            if 'pageSize=20' in url:
                url = url.replace('pageSize=20', f'pageSize={page_size}')
            
            result = run_rocketreach_web_crawl(url, headless, num_pages, page_size, timeout, start_page)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Web crawl completed: {result["total_contacts"]} contacts found, '
                        f'{result["saved_contacts"]} saved to database'
                    )
                )
                if debug_analyze:
                    self._analyze_snapshots()
            else:
                self.stdout.write(
                    self.style.ERROR(f'Web crawl failed: {result.get("error", "Unknown error")}')
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Web crawl error: {e}'))

    def _analyze_snapshots(self):
        """Analyze saved HTML snapshots and print quick diagnostics similar to the inline python check."""
        # Prefer the most recent employees page snapshot name we use
        candidates = [
            Path('rocketreach_employees_page.html'),
            Path('rocketreach_after_company_click.html'),
            Path('rocketreach_company_page.html')
        ]
        html_path = next((p for p in candidates if p.exists()), None)
        if not html_path:
            self.stdout.write('No snapshot HTML found to analyze.')
            return

        try:
            s = html_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed reading {html_path}: {e}'))
            return

        mails = re.findall(r'mailto:[^"\s]+', s)
        self.stdout.write(f'ANALYZE: FILE {html_path}')
        self.stdout.write(f'MAILTO_COUNT {len(mails)}')
        for m in mails[:10]:
            self.stdout.write(m)
        self.stdout.write(f'HAS_GET_CONTACT {("Get Contact Info" in s)}')

        try:
            soup = BeautifulSoup(s, 'html.parser')
            cards = soup.select('[data-profile-card-id]')
            self.stdout.write(f'CARDS {len(cards)}')
            sample_id = cards[0].get('data-profile-card-id') if cards else 'N/A'
            self.stdout.write(f'SAMPLE_CARD_ID {sample_id}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Card parse failed: {e}'))

    def handle_keyword_search(self, options):
        """Handle keyword search"""
        keyword = options['keyword']
        headless = options['headless']
        
        self.stdout.write(
            self.style.SUCCESS(f'Searching for keyword: {keyword}')
        )
        
        try:
            result = run_rocketreach_keyword_search(keyword, headless)
            
            if result['success']:
                emails = result.get('emails', [])
                if emails:
                    self.stdout.write(
                        self.style.SUCCESS(f'Found {len(emails)} email(s) for "{keyword}":')
                    )
                    for i, email in enumerate(emails, 1):
                        self.stdout.write(f'  {i}. {email}')
                else:
                    self.stdout.write(f'No emails found for "{keyword}"')
            else:
                self.stdout.write(
                    self.style.ERROR(f'Search failed: {result.get("error", "Unknown error")}')
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Search error: {e}'))

    def handle_sample_data(self, options):
        """Handle sample data creation"""
        url = options['url']
        start_page = options['start_page']
        num_pages = options['num_pages']
        page_size = options['page_size']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Creating sample contacts: {url}, pages {start_page}-{start_page + num_pages - 1}, size {page_size}'
            )
        )
        
        # Create sample contacts
        total_created = 0
        
        for page_num in range(start_page, start_page + num_pages):
            for i in range(page_size):
                try:
                    # Create sample contact
                    contact = RocketReachContact.objects.create(
                        email=f'lawyer{page_num}_{i+1}@example.com',
                        name=f'Lawyer {page_num}_{i+1}',
                        company=f'Law Firm {page_num}_{i+1}',
                        title=f'Attorney {i+1}',
                        location=f'City {page_num}_{i+1}, State',
                        profile_photo=f'https://example.com/photo{page_num}_{i+1}.jpg',
                        linkedin_url=f'https://linkedin.com/in/lawyer{page_num}_{i+1}',
                        twitter_url=f'https://twitter.com/lawyer{page_num}_{i+1}',
                        primary_email=f'primary{page_num}_{i+1}@example.com',
                        secondary_email=f'secondary{page_num}_{i+1}@example.com',
                        contact_grade='A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C',
                        work_experience=[
                            f'Attorney @ Law Firm {page_num}_{i+1}',
                            f'Associate @ Previous Firm {i+1}',
                            f'Intern @ Legal Clinic {i+1}'
                        ],
                        education=[
                            f'2020 - 2023 Juris Doctorate @ Law School {page_num}_{i+1}',
                            f'2016 - 2020 Bachelor of Arts @ University {i+1}'
                        ],
                        skills=f'Legal Research, Litigation, Contract Law, Family Law, Criminal Law, Civil Rights, Immigration Law, Corporate Law, Real Estate Law, Personal Injury, Workers Compensation, Employment Law, Bankruptcy, Estate Planning, Tax Law, Intellectual Property, Environmental Law, Health Care Law, Education Law, Government Law, International Law, Maritime Law, Military Law, Patent Law, Securities Law, Sports Law, Technology Law, Transportation Law, Veterans Law, White Collar Crime, Workers Compensation, Wrongful Death, Zoning Law',
                        profile_id=f'profile_{page_num}_{i+1}',
                        source_url=url,
                        page_number=page_num,
                        position_on_page=i + 1,
                        confidence_score=0.8,
                        status='unknown',
                        raw_data={
                            'profile_id': f'profile_{page_num}_{i+1}',
                            'extracted_from': 'sample_data_command',
                            'contact_grade': 'A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C',
                            'work_experience_count': 3,
                            'education_count': 2
                        }
                    )
                    
                    total_created += 1
                    
                    if total_created % 10 == 0:
                        self.stdout.write(f'Created {total_created} contacts...')
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating contact {page_num}_{i+1}: {e}'))
                    continue

        self.stdout.write(
            self.style.SUCCESS(f'Sample data creation completed: {total_created} contacts created')
        )
        
        # Show summary
        total_contacts = RocketReachContact.objects.count()
        self.stdout.write(f'Total contacts in database: {total_contacts}')
        
        # Show sample contacts
        recent_contacts = RocketReachContact.objects.order_by('-created_at')[:5]
        self.stdout.write('Recent contacts:')
        for contact in recent_contacts:
            self.stdout.write(f'  - {contact.name} ({contact.email}) - {contact.company} - Grade: {contact.contact_grade}')
