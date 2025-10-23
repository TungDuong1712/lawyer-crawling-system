"""
Management command to setup LawInfo SourceConfiguration with full selectors and start URLs
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
            'description': 'Crawl personal injury lawyers from LawInfo.com with comprehensive data extraction',
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
        
        # Comprehensive selectors data for LawInfo - divided into LIST and DETAIL
        selectors_data = {
            # LIST SELECTORS (for lawinfo.html - listing pages)
            "list": {
                # Basic lawyer information from listing cards
                "lawyer_name": "//h2[@class='listing-details-header']//a | //h3[@class='lawyer-name'] | //div[@class='firm-basics']//h2//a",
                
                "phone": "//a[@class='directory_phone']//span[contains(@class, 'd-none d-lg-inline-flex')] | //a[contains(@href, 'tel:')]//span[contains(@class, 'd-none d-lg-inline-flex')]",
                
                "company": "//h2[@class='listing-details-header']//a | //div[@class='firm-basics']//h2//a",
                
                "practice_area": "//span[@class='jobTitle'] | //div[@class='firm-secondary']//span[@class='jobTitle']",
                
                "location": "//span[@class='locality'] | //span[@class='region'] | //div[@class='firm-secondary']//span[@class='locality']",
                
                "description": "//p[@class='listing-desc-detail'] | //div[@class='listing-desc-detail']",
                
                "experience": "//span[@class='fw-bold text-dark-emphasis'] | //button[@class='number-badge']//span[@class='fw-bold text-dark-emphasis']",
                
                "detail_url": "//a[@class='directory_profile']/@href | //h2[@class='listing-details-header']//a/@href",
                
                "website_url": "//a[@class='directory_website']/@href",
                
                "contact_url": "//a[@class='directory_contact']/@href",
                
                "badges": "//div[@class='badges']//div[@class='number'] | //div[@class='number-badge']//div[@class='number']",
                
                "services": "//div[@class='listing-services']//p | //div[@class='listing-services']//span",
                
                "image": "//img[@class='img-thumbnail']/@src | //div[@class='listing-thumbnail-container']//img/@src"
            },
            
            # DETAIL SELECTORS (for lawinfo_detail.html - profile pages)
            "detail": {
                # Basic firm information
                "firm_name": "//h1[@class='org listing-details-header'] | //h1[contains(@class, 'listing-details-header')]",
                
                "phone": "//a[@class='listing-desc-phone profile-phone-header'] | //a[contains(@href, 'tel:')]",
                
                "address": "//p[@class='listing-desc-address'] | //div[@class='listing-desc-address']",
                
                "website": "//a[@class='detail-link profile-website-header']/@href | //a[contains(@href, 'http') and not(contains(@href, 'lawinfo.com'))]/@href",
                
                "practice_area": "//span[@class='jobTitle'] | //div[@class='listing-details-tagline']//span[@class='jobTitle']",
                
                "location": "//span[@class='locality'] | //span[@class='region'] | //div[@class='listing-details-tagline']//span[@class='locality']",
                
                "description": "//p[@class='listing-desc-detail'] | //div[@class='listing-desc-detail']",
                
                "experience": "//span[@class='fw-bold text-dark-emphasis'] | //button[@class='number-badge']//span[@class='fw-bold text-dark-emphasis']",
                
                "badges": "//div[@class='badges']//div[@class='number'] | //div[@class='number-badge']//div[@class='number']",
                
                "services": "//div[@class='listing-services']//p | //div[@class='listing-services']//span",
                
                "image": "//img[@class='img-thumbnail']/@src",
                
                # Attorney profiles section
                "attorney_name": "//h4[contains(text(), 'Attorney')] | //h4[contains(text(), 'Attorney')]//text()",
                
                "attorney_image": "//h4[contains(text(), 'Attorney')]//following-sibling::img/@src | //img[contains(@alt, 'Attorney')]/@src",
                
                "bar_admissions": "//h4[text()='Bar Admissions:']//following-sibling::ul//li | //div[contains(text(), 'Bar Admissions')]//following-sibling::ul//li",
                
                "education": "//h4[text()='Education:']//following-sibling::ul//li | //div[contains(text(), 'Education')]//following-sibling::ul//li",
                
                # Office locations
                "office_locations": "//div[@class='location-container']//a | //div[@class='col location-container']//a",
                
                "office_addresses": "//span[@class='street-address'] | //div[@class='location-container']//span[@class='street-address']",
                
                "office_cities": "//span[@class='locality'] | //div[@class='location-container']//span[@class='locality']",
                
                "office_states": "//span[@class='region'] | //div[@class='location-container']//span[@class='region']",
                
                "office_zip": "//span[@class='postal-code'] | //div[@class='location-container']//span[@class='postal-code']",
                
                # Lead Counsel section
                "lead_counsel_attorneys": "//h2[@class='h3'] | //div[@class='lc-attorney-record']//h2[@class='h3']",
                
                "lead_counsel_images": "//div[@class='lc-attorney-record']//img/@src | //img[contains(@alt, 'Attorney')]/@src",
                
                "lead_counsel_practice_areas": "//table[@class='table paragraph-default']//td[1] | //div[@class='lc-attorney-record']//table//td[1]",
                
                "lead_counsel_years": "//table[@class='table paragraph-default']//td[2] | //div[@class='lc-attorney-record']//table//td[2]",
                
                # Contact form
                "contact_form": "//form[@id='lawinfo_firm_contact_form'] | //form[contains(@action, 'process_contact')]",
                
                # Related practice areas and cities
                "related_practice_areas": "//ul[@aria-labelledby='card-related-pa-label']//a | //div[@class='related_pas']//ul//a",
                
                "related_cities": "//ul[@aria-labelledby='card-related-cities-label']//a | //div[@class='related_pas']//ul[2]//a"
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
        
