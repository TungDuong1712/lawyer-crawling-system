"""
Management command to setup SuperLawyers SourceConfiguration with full selectors and start URLs
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.crawler.models import SourceConfiguration


class Command(BaseCommand):
    help = "Set up SourceConfiguration, StartURL, and Selectors for SuperLawyers.com"

    def handle(self, *args, **options):
        # Setup source configuration data
        source_name = "SuperLawyers"
        
        # SourceConfiguration data
        config_data = {
            'name': 'SuperLawyers Family Law Attorneys',
            'description': 'Crawl family law attorneys from SuperLawyers.com with comprehensive data extraction',
            'status': 'PENDING',
            'delay_between_requests': 2.0,
            'max_retries': 3,
            'timeout': 30,
        }
        
        # Start URLs data - SuperLawyers Family Law URLs
        start_urls_data = [
            # New Mexico
            "https://attorneys.superlawyers.com/family-law/new-mexico/albuquerque/",
            
            # Georgia
            "https://attorneys.superlawyers.com/family-law/georgia/atlanta/",
            
            # Texas
            "https://attorneys.superlawyers.com/family-law/texas/austin/",
            "https://attorneys.superlawyers.com/family-law/texas/dallas/",
            "https://attorneys.superlawyers.com/family-law/texas/el-paso/",
            "https://attorneys.superlawyers.com/family-law/texas/fort-worth/",
            "https://attorneys.superlawyers.com/family-law/texas/houston/",
            "https://attorneys.superlawyers.com/family-law/texas/laredo/",
            "https://attorneys.superlawyers.com/family-law/texas/san-antonio/",
            
            # Maryland
            "https://attorneys.superlawyers.com/family-law/maryland/baltimore/",
            
            # Massachusetts
            "https://attorneys.superlawyers.com/family-law/massachusetts/boston/",
            
            # New York
            "https://attorneys.superlawyers.com/family-law/new-york/bronx/",
            "https://attorneys.superlawyers.com/family-law/new-york/brooklyn/",
            "https://attorneys.superlawyers.com/family-law/new-york/manhattan/",
            "https://attorneys.superlawyers.com/family-law/new-york/new-york/",
            "https://attorneys.superlawyers.com/family-law/new-york/queens/",
            "https://attorneys.superlawyers.com/family-law/new-york/staten-island/",
            
            # South Carolina
            "https://attorneys.superlawyers.com/family-law/south-carolina/charleston/",
            
            # North Carolina
            "https://attorneys.superlawyers.com/family-law/north-carolina/charlotte/",
            "https://attorneys.superlawyers.com/family-law/north-carolina/raleigh/",
            
            # Illinois
            "https://attorneys.superlawyers.com/family-law/illinois/chicago/",
            
            # Ohio
            "https://attorneys.superlawyers.com/family-law/ohio/cincinnati/",
            "https://attorneys.superlawyers.com/family-law/ohio/cleveland/",
            "https://attorneys.superlawyers.com/family-law/ohio/columbus/",
            
            # Colorado
            "https://attorneys.superlawyers.com/family-law/colorado/denver/",
            
            # Michigan
            "https://attorneys.superlawyers.com/family-law/michigan/detroit/",
            
            # Virginia
            "https://attorneys.superlawyers.com/family-law/virginia/fairfax/",
            "https://attorneys.superlawyers.com/family-law/virginia/virginia-beach/",
            
            # California
            "https://attorneys.superlawyers.com/family-law/california/fresno/",
            "https://attorneys.superlawyers.com/family-law/california/long-beach/",
            "https://attorneys.superlawyers.com/family-law/california/los-angeles/",
            "https://attorneys.superlawyers.com/family-law/california/riverside/",
            "https://attorneys.superlawyers.com/family-law/california/sacramento/",
            "https://attorneys.superlawyers.com/family-law/california/san-diego/",
            "https://attorneys.superlawyers.com/family-law/california/san-francisco/",
            "https://attorneys.superlawyers.com/family-law/california/san-jose/",
            
            # Indiana
            "https://attorneys.superlawyers.com/family-law/indiana/indianapolis/",
            
            # Florida
            "https://attorneys.superlawyers.com/family-law/florida/jacksonville/",
            "https://attorneys.superlawyers.com/family-law/florida/miami/",
            "https://attorneys.superlawyers.com/family-law/florida/orlando/",
            "https://attorneys.superlawyers.com/family-law/florida/tampa/",
            
            # Missouri
            "https://attorneys.superlawyers.com/family-law/missouri/kansas-city/",
            
            # Nevada
            "https://attorneys.superlawyers.com/family-law/nevada/las-vegas/",
            
            # Kentucky
            "https://attorneys.superlawyers.com/family-law/kentucky/louisville/",
            
            # Louisiana
            "https://attorneys.superlawyers.com/family-law/louisiana/new-orleans/",
            
            # Tennessee
            "https://attorneys.superlawyers.com/family-law/tennessee/memphis/",
            "https://attorneys.superlawyers.com/family-law/tennessee/nashville/",
            
            # Wisconsin
            "https://attorneys.superlawyers.com/family-law/wisconsin/milwaukee/",
            
            # Minnesota
            "https://attorneys.superlawyers.com/family-law/minnesota/minneapolis/",
            
            # New Jersey
            "https://attorneys.superlawyers.com/family-law/new-jersey/newark/",
            
            # Oklahoma
            "https://attorneys.superlawyers.com/family-law/oklahoma/oklahoma-city/",
            "https://attorneys.superlawyers.com/family-law/oklahoma/tulsa/",
            
            # Pennsylvania
            "https://attorneys.superlawyers.com/family-law/pennsylvania/philadelphia/",
            "https://attorneys.superlawyers.com/family-law/pennsylvania/pittsburgh/",
            
            # Oregon
            "https://attorneys.superlawyers.com/family-law/oregon/portland/",
            
            # Arizona
            "https://attorneys.superlawyers.com/family-law/arizona/mesa/",
            "https://attorneys.superlawyers.com/family-law/arizona/phoenix/",
            "https://attorneys.superlawyers.com/family-law/arizona/tucson/",
            
            # Washington
            "https://attorneys.superlawyers.com/family-law/washington/seattle/",
            
            # Washington DC
            "https://attorneys.superlawyers.com/family-law/washington-dc/washington/",
        ]
        
        # Comprehensive selectors data for SuperLawyers - divided into LIST and DETAIL
        selectors_data = {
            # LIST SELECTORS (for superlawyers.html - listing pages)
            "list": {
                # Basic attorney information from listing cards
                "attorney_name": "//h2[@class='full-name']//a | //h2[@class='full-name fw-bold']//a",
                "phone": "//a[@class='directory_phone'] | //a[contains(@href, 'tel:')]",
                "firm_name": "//span[@class='d-block fw-bold text-secondary'] | //a[@class='single-link directory_website']",
                "practice_area": "//span[@class='top_lawyer_pa'] | //span[contains(@class, 'top_lawyer_pa')]",
                "location": "//span[@class='city'] | //span[contains(@class, 'city')]",
                "description": "//p[@class='ts_tagline'] | //div[contains(@class, 'ts_tagline')]",
                "detail_url": "//a[@class='directory_profile']/@href | //h2[@class='full-name']//a/@href",
                "website_url": "//a[@class='directory_website']/@href | //a[@class='single-link directory_website']/@href",
                "contact_url": "//a[@class='directory_contact']/@href",
                "image": "//img[contains(@alt, 'attorney')]/@src | //img[contains(@class, 'w-100 rounded-3')]/@src",
                "badges": "//span[@class='selected_to'] | //span[contains(@class, 'selected_to')]",
                "sponsored": "//span[@class='top_lawyer_pa paragraph-xsmall d-block mb-2']//i[contains(@class, 'icon-ribbon')]"
            },

            # DETAIL SELECTORS (for superlawyers_detail.html - profile pages)
            "detail": {
                # Basic attorney information
                "attorney_name": "//h1[@id='attorney_name'] | //h1[@class='display-1']",
                "phone": "//span[contains(text(), 'Phone:')] | //div[contains(text(), 'Phone:')]",
                "email": "//a[@class='profile-contact-header']/@href | //a[contains(@href, 'contact/lawyer')]",
                "address": "//div[@class='card-body']//text()[contains(., 'Dr')] | //div[contains(text(), 'Dr')]",
                "firm_name": "//a[@class='profile-profile-header'] | //h2[@class='fw-bold paragraph-default']",
                "website": "//a[@class='profile-website-header']/@href | //a[contains(@href, 'http') and not(contains(@href, 'superlawyers.com'))]/@href",
                "practice_area": "//span[@id='pa_areas'] | //p[@id='pa_areas']",
                "location": "//h2[@id='attorney_profile_tagline'] | //h2[contains(@class, 'paragraph-large')]",
                "description": "//h2[@id='attorney_profile_tagline'] | //h2[contains(@class, 'paragraph-large')]",
                "experience": "//p[@id='licensed_since'] | //p[contains(text(), 'Licensed')]",
                "education": "//p[@id='law_school'] | //p[contains(text(), 'Education')]",
                "image": "//img[@class='w-100 rounded-3 h-auto']/@src | //img[contains(@alt, 'attorney')]/@src",

                # SuperLawyers specific information
                "super_lawyer_years": "//span[contains(text(), 'Selected to Super Lawyers')] | //span[contains(@class, 'fst-italic')]",
                "super_lawyer_badge": "//img[contains(@src, 'icon-sl-selection.svg')] | //span[contains(text(), 'Super Lawyers')]",
                "rising_star": "//span[contains(text(), 'Rising Star')] | //span[contains(text(), 'Rising Stars')]",

                # Contact information
                "contact_form": "//a[@class='profile-contact-header'] | //a[contains(@href, 'contact/lawyer')]",
                "website_link": "//a[@class='profile-website-header'] | //a[contains(@href, 'http') and not(contains(@href, 'superlawyers.com'))]",

                # Professional details
                "licensed_since": "//p[@id='licensed_since'] | //p[contains(text(), 'Licensed')]",
                "law_school": "//p[@id='law_school']//a | //p[contains(text(), 'Education')]//a",
                "bar_admissions": "//p[contains(text(), 'Licensed')] | //span[contains(text(), 'Licensed')]",

                # Additional metadata
                "profile_url": "//a[@class='profile-profile-header']/@href | //a[contains(@href, 'lawfirm')]/@href",
                "firm_profile": "//a[@class='profile-profile-header']/@href | //a[contains(@href, 'lawfirm')]/@href"
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
        
        self.stdout.write(f"\n🚀 Ready to start crawling!")
        self.stdout.write(f"   - Access admin: http://localhost:8001/admin/crawler/sourceconfiguration/")
        self.stdout.write(f"   - Start crawling: Use admin actions or management commands")
        self.stdout.write(f"   - Monitor progress: Check progress_percentage field")
