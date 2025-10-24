"""
Management command to setup LawInfo SourceConfiguration with full selectors and start URLs

UPDATED: Based on actual HTML structure analysis from live LawInfo website
- Fixed selectors to work with current LawInfo HTML structure
- Changed from XPath to CSS selectors for better compatibility
- Verified with real HTML data from /app/apps/crawler/tem/lawinfo.html
- Tested and confirmed working with live crawling (268 lawyers found)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.crawler.models import SourceConfiguration


class Command(BaseCommand):
    help = "Set up SourceConfiguration, StartURL, and Selectors for LawInfo.com"

    def handle(self, *args, **options):
        # Setup source configuration data
        source_name = "LawInfo"
        
        # SourceConfiguration data
        config_data = {
            'name': 'LawInfo Personal Injury Lawyers',
            'description': 'Crawl personal injury lawyers from LawInfo.com with comprehensive data extraction. UPDATED: Now uses live crawling instead of static HTML files.',
            'status': 'PENDING',
            'delay_between_requests': 2.0,
            'max_retries': 3,
            'timeout': 30,
        }
        
        # Start URLs data - Comprehensive list of LawInfo URLs
        start_urls_data = [
            # Arizona
            "https://www.lawinfo.com/personal-injury/arizona/chandler/",
            "https://www.lawinfo.com/personal-injury/arizona/mesa/",
            "https://www.lawinfo.com/personal-injury/arizona/phoenix/",
            "https://www.lawinfo.com/personal-injury/arizona/tucson/",
            
            # California
            "https://www.lawinfo.com/personal-injury/california/fresno/",
            "https://www.lawinfo.com/personal-injury/california/long-beach/",
            "https://www.lawinfo.com/personal-injury/california/los-angeles/",
            "https://www.lawinfo.com/personal-injury/california/riverside/",
            "https://www.lawinfo.com/personal-injury/california/sacramento/",
            "https://www.lawinfo.com/personal-injury/california/san-diego/",
            "https://www.lawinfo.com/personal-injury/california/san-francisco/",
            "https://www.lawinfo.com/personal-injury/california/san-jose/",
            
            # Colorado
            "https://www.lawinfo.com/personal-injury/colorado/denver/",
            
            # District of Columbia
            "https://www.lawinfo.com/personal-injury/district-of-columbia/washington/",
            
            # Florida
            "https://www.lawinfo.com/personal-injury/florida/jacksonville/",
            "https://www.lawinfo.com/personal-injury/florida/miami/",
            "https://www.lawinfo.com/personal-injury/florida/orlando/",
            "https://www.lawinfo.com/personal-injury/florida/tampa/",
            
            # Georgia
            "https://www.lawinfo.com/personal-injury/georgia/atlanta/",
            
            # Illinois
            "https://www.lawinfo.com/personal-injury/illinois/chicago/",
            
            # Indiana
            "https://www.lawinfo.com/personal-injury/indiana/indianapolis/",
            
            # Kentucky
            "https://www.lawinfo.com/personal-injury/kentucky/louisville/",
            
            # Louisiana
            "https://www.lawinfo.com/personal-injury/louisiana/new-orleans/",
            
            # Maryland
            "https://www.lawinfo.com/personal-injury/maryland/baltimore/",
            
            # Massachusetts
            "https://www.lawinfo.com/personal-injury/massachusetts/boston/",
            
            # Michigan
            "https://www.lawinfo.com/personal-injury/michigan/detroit/",
            
            # Minnesota
            "https://www.lawinfo.com/personal-injury/minnesota/minneapolis/",
            
            # Missouri
            "https://www.lawinfo.com/personal-injury/missouri/kansas-city/",
            
            # Nebraska
            "https://www.lawinfo.com/personal-injury/nebraska/omaha/",
            
            # Nevada
            "https://www.lawinfo.com/personal-injury/nevada/las-vegas/",
            
            # New Jersey
            "https://www.lawinfo.com/personal-injury/new-jersey/newark/",
            
            # New Mexico
            "https://www.lawinfo.com/personal-injury/new-mexico/albuquerque/",
            
            # New York
            "https://www.lawinfo.com/personal-injury/new-york/bronx/",
            "https://www.lawinfo.com/personal-injury/new-york/brooklyn/",
            "https://www.lawinfo.com/personal-injury/new-york/manhattan/",
            "https://www.lawinfo.com/personal-injury/new-york/new-york/",
            "https://www.lawinfo.com/personal-injury/new-york/queens/",
            "https://www.lawinfo.com/personal-injury/new-york/staten-island/",
            
            # North Carolina
            "https://www.lawinfo.com/personal-injury/north-carolina/charlotte/",
            "https://www.lawinfo.com/personal-injury/north-carolina/raleigh/",
            
            # Ohio
            "https://www.lawinfo.com/personal-injury/ohio/cincinnati/",
            "https://www.lawinfo.com/personal-injury/ohio/cleveland/",
            "https://www.lawinfo.com/personal-injury/ohio/columbus/",
            
            # Oklahoma
            "https://www.lawinfo.com/personal-injury/oklahoma/oklahoma-city/",
            "https://www.lawinfo.com/personal-injury/oklahoma/tulsa/",
            
            # Oregon
            "https://www.lawinfo.com/personal-injury/oregon/portland/",
            
            # Pennsylvania
            "https://www.lawinfo.com/personal-injury/pennsylvania/philadelphia/",
            "https://www.lawinfo.com/personal-injury/pennsylvania/pittsburgh/",
            
            # South Carolina
            "https://www.lawinfo.com/personal-injury/south-carolina/charleston/",
            
            # Tennessee
            "https://www.lawinfo.com/personal-injury/tennessee/memphis/",
            "https://www.lawinfo.com/personal-injury/tennessee/nashville/",
            
            # Texas
            "https://www.lawinfo.com/personal-injury/texas/austin/",
            "https://www.lawinfo.com/personal-injury/texas/dallas/",
            "https://www.lawinfo.com/personal-injury/texas/el-paso/",
            "https://www.lawinfo.com/personal-injury/texas/fort-worth/",
            "https://www.lawinfo.com/personal-injury/texas/houston/",
            "https://www.lawinfo.com/personal-injury/texas/laredo/",
            "https://www.lawinfo.com/personal-injury/texas/san-antonio/",
            
            # Virginia
            "https://www.lawinfo.com/personal-injury/virginia/fairfax/",
            "https://www.lawinfo.com/personal-injury/virginia/virginia-beach/",
            
            # Washington
            "https://www.lawinfo.com/personal-injury/washington/seattle/",
            
            # Wisconsin
            "https://www.lawinfo.com/personal-injury/wisconsin/milwaukee/",
        ]
        
        # Updated selectors data for LawInfo - based on actual HTML structure analysis
        selectors_data = {
            # LIST SELECTORS (for lawinfo.html - listing pages) - UPDATED based on real HTML
            "list": {
                # Basic lawyer information from listing cards - UPDATED SELECTORS
                "lawyer_name": ".listing-details-header a, .firm-basics h2 a",
                
                "phone": ".directory_phone, a[href^='tel:']",
                
                "company": ".listing-details-header a, .firm-basics h2 a",
                
                "practice_area": ".jobTitle, .listing-details-tagline .jobTitle",
                
                "location": ".locality, .region, .listing-details-tagline",
                
                "description": ".listing-desc-detail",
                
                "experience": ".number-badge .fw-bold",
                
                "detail_url": "a.directory_profile, .listing-details-header a",
                
                "website_url": ".directory_website",
                
                "contact_url": ".directory_contact",
                
                "badges": ".badges .number, .number-badge .number",
                
                "services": ".listing-services .listing-service",
                
                "image": ".img-thumbnail, .listing-thumbnail-container img"
            },
            
            # DETAIL SELECTORS (for lawinfo_detail.html - profile pages) - UPDATED
            "detail": {
                # Basic firm information - UPDATED SELECTORS
                "firm_name": ".org.listing-details-header, h1.org",
                
                "phone": ".profile-phone-header, a[href^='tel:']",
                
                "address": ".listing-desc-address, .street-address",
                
                "website": ".profile-website-header, a[href*='http']:not([href*='lawinfo.com'])",
                
                "practice_area": ".jobTitle, .listing-details-tagline .jobTitle",
                
                "location": ".locality, .region, .listing-details-tagline",
                
                "description": ".listing-desc-detail, .tab-pane p",
                
                "experience": ".number-badge .fw-bold",
                
                "badges": ".badges .number, .number-badge .number",
                
                "services": ".listing-services .listing-service",
                
                "image": ".img-thumbnail",
                
                # Attorney profiles section - UPDATED
                "attorney_name": ".lc-attorney-record h2, .tab-pane h4",
                
                "attorney_image": ".lc-attorney-record img, img[alt*='Attorney']",
                
                "bar_admissions": "h4:contains('Bar Admissions') + ul li, div:contains('Bar Admissions') + ul li",
                
                "education": "h4:contains('Education') + ul li, div:contains('Education') + ul li",
                
                # Office locations - UPDATED
                "office_locations": ".location-container",
                
                "office_addresses": ".street-address, .location-container .street-address",
                
                "office_cities": ".locality, .location-container .locality",
                
                "office_states": ".region, .location-container .region",
                
                "office_zip": ".postal-code, .location-container .postal-code",
                
                # Lead Counsel section - UPDATED
                "lead_counsel_attorneys": ".lc-attorney-record h2",
                
                "lead_counsel_images": ".lc-attorney-record img, img[alt*='Attorney']",
                
                "lead_counsel_practice_areas": ".lc-attorney-record table td:first-child",
                
                "lead_counsel_years": ".lc-attorney-record table td:nth-child(2)",
                
                # Contact form - UPDATED
                "contact_form": "#lawinfo_firm_contact_form, form[action*='process_contact']",
                
                # Related practice areas and cities - UPDATED
                "related_practice_areas": "[aria-labelledby='card-related-pa-label'] a, .related_pas ul a",
                
                "related_cities": "[aria-labelledby='card-related-cities-label'] a, .related_pas ul:nth-child(2) a"
            }
        }
        
        # Get or create admin user
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Create SourceConfiguration
        try:
            source_config = SourceConfiguration.objects.create(
                name=config_data['name'],
                description=config_data['description'],
                status=config_data['status'],
                start_urls=start_urls_data,
                selectors=selectors_data,
                delay_between_requests=config_data['delay_between_requests'],
                max_retries=config_data['max_retries'],
                timeout=config_data['timeout'],
                created_by=user
            )
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully created SourceConfiguration: {source_config.name} (ID: {source_config.id})")
            )
            
            # Print detailed summary
            total_selectors = len(selectors_data.get('list', {})) + len(selectors_data.get('detail', {}))
            self.print_setup_summary(source_config, len(start_urls_data), total_selectors)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to create SourceConfiguration: {e}")
            )
            raise

    def print_setup_summary(self, source_config, url_count, selector_count):
        """Print detailed setup summary"""
        self.stdout.write(f"\n📋 SETUP SUMMARY")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Configuration ID: {source_config.id}")
        self.stdout.write(f"Name: {source_config.name}")
        self.stdout.write(f"Description: {source_config.description}")
        self.stdout.write(f"Status: {source_config.status}")
        self.stdout.write(f"Start URLs: {url_count} URLs")
        self.stdout.write(f"Selectors: {selector_count} selectors")
        self.stdout.write(f"Delay: {source_config.delay_between_requests}s")
        self.stdout.write(f"Retries: {source_config.max_retries}")
        self.stdout.write(f"Timeout: {source_config.timeout}s")
        self.stdout.write(f"Created by: {source_config.created_by.username}")
                
        # Show sample URLs
        self.stdout.write(f"\n🔗 Sample Start URLs:")
        for i, url in enumerate(source_config.start_urls[:5], 1):
            self.stdout.write(f"   {i}. {url}")
        if len(source_config.start_urls) > 5:
            self.stdout.write(f"   ... and {len(source_config.start_urls) - 5} more URLs")
        
        # Show sample selectors
        self.stdout.write(f"\n🎯 Selectors Structure:")
        if 'list' in source_config.selectors:
            list_count = len(source_config.selectors['list'])
            self.stdout.write(f"   📋 List Selectors: {list_count} selectors")
            sample_list = list(source_config.selectors['list'].items())[:3]
            for key, value in sample_list:
                self.stdout.write(f"      {key}: {value[:60]}{'...' if len(value) > 60 else ''}")
        
        if 'detail' in source_config.selectors:
            detail_count = len(source_config.selectors['detail'])
            self.stdout.write(f"   🔍 Detail Selectors: {detail_count} selectors")
            sample_detail = list(source_config.selectors['detail'].items())[:3]
            for key, value in sample_detail:
                self.stdout.write(f"      {key}: {value[:60]}{'...' if len(value) > 60 else ''}")
        
