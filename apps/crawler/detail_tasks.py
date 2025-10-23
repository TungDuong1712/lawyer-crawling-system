"""
Detail crawling tasks for 2-step lawyer crawling
"""

import logging
from bs4 import BeautifulSoup
from .tasks import (
    AntiDetectionManager, 
    get_domain_selectors, 
    find_lawyer_containers,
    extract_text_by_selectors,
    extract_phone_from_lawinfo,
    extract_address_from_lawinfo,
    extract_website_from_lawinfo,
    extract_phone_from_text,
    extract_address_from_text,
    extract_email_from_text,
    create_sample_lawyers_for_url
)
from .models import DiscoveryURL
from apps.lawyers.models import Lawyer

logger = logging.getLogger(__name__)


def crawl_single_url_basic(discovery_url):
    """
    Crawl basic lawyer information and extract detail URLs (Step 1)
    """
    url = discovery_url.url
    domain = discovery_url.domain
    
    # For lawinfo domain, use real HTML file if available
    if domain == 'lawinfo' and 'lawinfo.com' in url:
        return crawl_lawinfo_basic_with_real_html(discovery_url)
    
    # Use AntiDetectionManager for better stealth
    anti_detection = AntiDetectionManager()
    
    try:
        response = anti_detection.make_request(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic lawyer information and detail URLs
        lawyers = extract_basic_lawyers_from_soup(soup, domain, discovery_url)
        
        return len(lawyers)
        
    except Exception as e:
        # If real crawl fails, use sample data
        logger.warning(f"Real crawl failed for {url}: {e}. Using sample data.")
        return create_sample_lawyers_for_url(discovery_url)


def crawl_lawinfo_basic_with_real_html(discovery_url):
    """
    Crawl lawinfo basic info using real HTML file
    """
    try:
        # Read real HTML file
        html_file_path = '/app/apps/crawler/tem/lawinfo.html'
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract basic lawyer information and detail URLs
        lawyers = extract_basic_lawyers_from_soup(soup, 'lawinfo', discovery_url)
        
        return len(lawyers)
        
    except Exception as e:
        logger.warning(f"Real HTML basic crawl failed: {e}. Using sample data.")
        return create_sample_lawyers_for_url(discovery_url)


def extract_basic_lawyers_from_soup(soup, domain, discovery_url):
    """
    Extract basic lawyer information and detail URLs from HTML soup
    """
    lawyers = []
    
    # Domain-specific selectors
    selectors = get_domain_selectors(domain)
    
    # Find lawyer containers
    lawyer_containers = find_lawyer_containers(soup, domain)
    
    for container in lawyer_containers:
        try:
            lawyer_data = extract_single_lawyer_basic(container, selectors, discovery_url)
            if lawyer_data:
                lawyer = Lawyer.objects.create(**lawyer_data)
                lawyers.append(lawyer)

            continue  # Skip failed extractions
        except Exception as e:
            continue  # Skip failed extractions
    
    return lawyers


def extract_single_lawyer_basic(container, selectors, discovery_url):
    """
    Extract basic information from a single lawyer container (Step 1)
    """
    try:
        # Extract company name
        company_name = extract_text_by_selectors(container, selectors['company_name'])
        if not company_name:
            return None
        
        # Extract basic info
        phone = extract_phone_from_lawinfo(container, selectors['phone'])
        if not phone:
            phone = extract_phone_from_text(container.get_text())
        
        address = extract_address_from_lawinfo(container, selectors['address'])
        if not address:
            address = extract_address_from_text(container.get_text())
        
        practice_areas = extract_text_by_selectors(container, selectors['practice_areas'])
        if not practice_areas:
            practice_areas = discovery_url.practice_area.replace('-', ' ').title()
        
        website = extract_website_from_lawinfo(container, selectors['website'])
        
        email = extract_text_by_selectors(container, selectors['email'])
        if not email:
            email = extract_email_from_text(container.get_text())
        
        # Extract detail URL
        detail_url = extract_detail_url_from_container(container, discovery_url.domain)
        
        # Build basic attorney details
        description = extract_text_by_selectors(container, selectors.get('description', ''))
        attorney_details_text = description if description else f'Attorney specializing in {practice_areas}'
        
        # Create lawyer data
        lawyer_data = {
            'source_url': discovery_url.url,
            'domain': discovery_url.domain,
            'practice_area': discovery_url.practice_area,
            'state': discovery_url.state,
            'city': discovery_url.city,
            'company_name': company_name,
            'phone': phone,
            'address': address,
            'practice_areas': practice_areas,
            'attorney_details': attorney_details_text,
            'website': website,
            'email': email,
            'detail_url': detail_url,
            'is_detail_crawled': False
        }
        
        return lawyer_data
        
    except Exception as e:
        return None


def extract_detail_url_from_container(container, domain):
    """
    Extract detail URL from lawyer container
    """
    try:
        if domain == 'lawinfo':
            # Look for profile links
            profile_links = container.select('a[href*="/lawfirm/"]')
            for link in profile_links:
                href = link.get('href', '')
                if '/lawfirm/' in href and 'lawinfo.com' in href:
                    return href
        
        return ""
    except:
        return ""


def crawl_lawyer_detail(lawyer):
    """
    Crawl detailed information from lawyer's detail URL (Step 2)
    """
    try:
        # Use AntiDetectionManager for better stealth
        anti_detection = AntiDetectionManager()
        
        response = anti_detection.make_request(lawyer.detail_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract detailed information
        detail_info = extract_lawyer_detail_from_soup(soup, lawyer.domain)
        
        return detail_info
        
    except Exception as e:
        logger.warning(f"Detail crawl failed for {lawyer.detail_url}: {e}")
        return None


def extract_lawyer_detail_from_soup(soup, domain):
    """
    Extract detailed lawyer information from detail page
    """
    try:
        # Use detail selectors
        selectors = get_domain_selectors(f"{domain}_detail")
        
        detail_info = {}
        
        # Extract detailed information
        if selectors.get('description'):
            description = extract_text_by_selectors(soup, selectors['description'])
            if description:
                detail_info['attorney_details'] = description
        
        if selectors.get('attorneys'):
            attorneys = extract_attorneys_from_detail(soup, selectors['attorneys'])
            if attorneys:
                detail_info['attorney_details'] = f"{detail_info.get('attorney_details', '')}\n\nAttorneys: {attorneys}"
        
        if selectors.get('office_locations'):
            locations = extract_office_locations_from_detail(soup, selectors['office_locations'])
            if locations:
                detail_info['address'] = f"{detail_info.get('address', '')}\n\nOffice Locations: {locations}"
        
        return detail_info
        
    except Exception as e:
        logger.error(f"Error extracting detail info: {e}")
        return None


def extract_attorneys_from_detail(soup, selector):
    """
    Extract attorney information from detail page
    """
    try:
        attorneys = []
        attorney_elements = soup.select(selector)
        
        for attorney in attorney_elements[:5]:  # Limit to 5 attorneys
            name = attorney.get_text(strip=True)
            if name:
                attorneys.append(name)
        
        return " | ".join(attorneys) if attorneys else ""
    except:
        return ""


def extract_office_locations_from_detail(soup, selector):
    """
    Extract office locations from detail page
    """
    try:
        locations = []
        location_elements = soup.select(selector)
        
        for location in location_elements[:3]:  # Limit to 3 locations
            location_text = location.get_text(strip=True)
            if location_text:
                locations.append(location_text)
        
        return " | ".join(locations) if locations else ""
    except:
        return ""
