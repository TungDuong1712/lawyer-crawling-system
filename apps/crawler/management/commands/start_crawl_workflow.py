"""
Django management command to start the complete lawyer crawling workflow
Based on car crawling project experience
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.crawler.models import SourceConfiguration, DiscoveryURL, CrawlTemplate
from apps.lawyers.models import Lawyer
from apps.tasks.models import ScheduledTask
import time
from datetime import datetime


class Command(BaseCommand):
    help = 'Start complete lawyer crawling workflow (S1 + S2)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-name',
            type=str,
            default='Auto Crawl Session',
            help='Name for the crawl session'
        )
        parser.add_argument(
            '--domains',
            nargs='+',
            default=['lawinfo', 'superlawyers'],
            help='Domains to crawl (lawinfo, superlawyers, avvo)'
        )
        parser.add_argument(
            '--states',
            nargs='+',
            default=['new-mexico', 'texas'],
            help='States to crawl'
        )
        parser.add_argument(
            '--practice-areas',
            nargs='+',
            default=['car-accident', 'business-litigation'],
            help='Practice areas to crawl'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of URLs to crawl'
        )
        parser.add_argument(
            '--config',
            type=str,
            default='default',
            help='Crawl configuration to use'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Lawyer Crawling Workflow')
        )
        self.stdout.write('=' * 50)

        # S1: Find StartURLs
        self.stdout.write('\n📋 S1: Finding StartURLs...')
        start_urls = self.find_start_urls(
            domains=options['domains'],
            states=options['states'],
            practice_areas=options['practice_areas']
        )
        
        self.stdout.write(f'✅ Found {len(start_urls)} start URLs')
        
        # Create crawl session
        session = self.create_crawl_session(
            name=options['session_name'],
            domains=options['domains'],
            states=options['states'],
            practice_areas=options['practice_areas'],
            limit=options['limit']
        )
        
        # S2: Crawl Company Info
        self.stdout.write('\n🔄 S2: Crawling Company Information...')
        self.crawl_company_info(session, start_urls[:options['limit']])
        
        # Summary
        self.show_summary(session)

    def find_start_urls(self, domains, states, practice_areas):
        """S1: Generate start URLs based on domains, states, and practice areas"""
        start_urls = []
        
        # URL patterns based on car project experience
        url_patterns = {
            'lawinfo': 'https://www.lawinfo.com/{practice_area}/{state}/{city}/',
            'superlawyers': 'https://attorneys.superlawyers.com/{practice_area}/{state}/{city}/',
            'avvo': 'https://www.avvo.com/attorneys/{state}/{city}/{practice_area}'
        }
        
        # Cities for each state (based on car project data)
        state_cities = {
            'new-mexico': ['albuquerque', 'santa-fe', 'las-cruces', 'roswell'],
            'texas': ['houston', 'dallas', 'austin', 'san-antonio'],
            'california': ['los-angeles', 'san-francisco', 'san-diego', 'sacramento'],
            'florida': ['miami', 'orlando', 'tampa', 'jacksonville'],
            'new-york': ['new-york', 'buffalo', 'rochester', 'albany']
        }
        
        for domain in domains:
            for state in states:
                cities = state_cities.get(state, [])
                for city in cities:
                    for practice_area in practice_areas:
                        if domain in url_patterns:
                            url = url_patterns[domain].format(
                                practice_area=practice_area,
                                state=state,
                                city=city
                            )
                            start_urls.append({
                                'url': url,
                                'domain': domain,
                                'state': state,
                                'city': city,
                                'practice_area': practice_area
                            })
        
        return start_urls

    def create_crawl_session(self, name, domains, states, practice_areas, limit):
        """Create a new crawl session"""
        from django.contrib.auth.models import User
        
        # Get or create admin user
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        
        session = SourceConfiguration.objects.create(
            name=name,
            description=f'Automated crawl session for {", ".join(domains)} domains',
            status='pending',
            created_by=admin_user,
            domains=domains,
            states=states,
            practice_areas=practice_areas,
            limit=limit,
            total_urls=0,  # Will be updated
            crawled_urls=0,
            success_count=0,
            error_count=0
        )
        
        self.stdout.write(f'✅ Created crawl session: {session.name}')
        return session

    def crawl_company_info(self, session, start_urls):
        """S2: Crawl company information from start URLs"""
        from apps.crawler.tasks import crawl_lawyer_info_task
        
        self.stdout.write(f'🔄 Starting crawl of {len(start_urls)} URLs...')
        
        # Create crawl tasks
        tasks = []
        for url_info in start_urls:
            task = DiscoveryURL.objects.create(
                source_config=session,
                url=url_info['url'],
                domain=url_info['domain'],
                state=url_info['state'],
                city=url_info['city'],
                practice_area=url_info['practice_area'],
                status='pending'
            )
            tasks.append(task)
        
        # Update session
        session.total_urls = len(tasks)
        session.status = 'running'
        session.started_at = datetime.now()
        session.save()
        
        # Start crawling (simulate for now)
        success_count = 0
        error_count = 0
        
        for i, task in enumerate(tasks):
            self.stdout.write(f'   Crawling {i+1}/{len(tasks)}: {task.domain} - {task.practice_area}')
            
            try:
                # Simulate crawling (replace with actual crawl logic)
                time.sleep(0.1)  # Simulate processing time
                
                # Create sample lawyer data
                lawyer = Lawyer.objects.create(
                    source_url=task.url,
                    domain=task.domain,
                    practice_area=task.practice_area,
                    state=task.state,
                    city=task.city,
                    company_name=f'Sample Law Firm {i+1}',
                    phone=f'({555 + i}) {100 + i}-{2000 + i}',
                    address=f'{100 + i} Main St, {task.city.title()}, {task.state.title()}',
                    practice_areas=task.practice_area.replace('-', ' ').title(),
                    attorney_details=f'Experienced attorney in {task.practice_area.replace("-", " ")} law',
                    website=f'https://samplelaw{i+1}.com',
                    email=f'info@samplelaw{i+1}.com'
                )
                
                task.status = 'completed'
                task.lawyers_found = 1
                success_count += 1
                
            except Exception as e:
                task.status = 'failed'
                task.error_message = str(e)
                error_count += 1
                self.stdout.write(f'   ❌ Error: {e}')
            
            task.completed_at = datetime.now()
            task.save()
        
        # Update session
        session.crawled_urls = len(tasks)
        session.success_count = success_count
        session.error_count = error_count
        session.status = 'completed'
        session.completed_at = datetime.now()
        session.save()

    def show_summary(self, session):
        """Show crawl summary"""
        self.stdout.write('\n📊 CRAWL SUMMARY')
        self.stdout.write('=' * 30)
        self.stdout.write(f'Session: {session.name}')
        self.stdout.write(f'Status: {session.status}')
        self.stdout.write(f'Total URLs: {session.total_urls}')
        self.stdout.write(f'Crawled URLs: {session.crawled_urls}')
        self.stdout.write(f'Success: {session.success_count}')
        self.stdout.write(f'Errors: {session.error_count}')
        
        # Show lawyers found
        lawyers_count = Lawyer.objects.filter(
            source_url__in=[task.url for task in session.discovery_urls.all()]
        ).count()
        self.stdout.write(f'Lawyers Found: {lawyers_count}')
        
        self.stdout.write('\n🎉 Crawl workflow completed!')
        self.stdout.write('🌐 View results at: http://localhost:8001/admin/')
