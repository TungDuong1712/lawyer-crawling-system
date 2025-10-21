"""
Configuration for lawyer data crawling system
"""

# Domains to crawl
LAW_DOMAINS = {
    "lawinfo": {
        "base_url": "https://www.lawinfo.com",
        "url_pattern": "{base_url}/{practice_area}/{state}/{city}/",
        "selectors": {
            "company_name": ".firm-name, .attorney-name",
            "phone": ".phone, .contact-phone",
            "address": ".address, .location",
            "practice_areas": ".practice-areas, .specialties",
            "attorney_details": ".attorney-info, .lawyer-details",
            "website": ".website, .firm-website",
            "email": ".email, .contact-email"
        }
    },
    "superlawyers": {
        "base_url": "https://attorneys.superlawyers.com",
        "url_pattern": "{base_url}/{practice_area}/{state}/{city}/",
        "selectors": {
            "company_name": ".attorney-name, .firm-name",
            "phone": ".phone-number, .contact-info .phone",
            "address": ".address, .location-info",
            "practice_areas": ".practice-areas, .specialties",
            "attorney_details": ".attorney-bio, .profile-info",
            "website": ".website-link, .firm-website",
            "email": ".email-address, .contact-email"
        }
    },
    "avvo": {
        "base_url": "https://www.avvo.com",
        "url_pattern": "{base_url}/attorneys/{state}/{city}/{practice_area}",
        "selectors": {
            "company_name": ".attorney-name, .lawyer-name",
            "phone": ".phone, .contact-phone",
            "address": ".address, .office-location",
            "practice_areas": ".practice-areas, .specialties",
            "attorney_details": ".attorney-profile, .bio",
            "website": ".website, .firm-site",
            "email": ".email, .contact-email"
        }
    }
}

# States and cities
STATES_CITIES = {
    "new-mexico": ["albuquerque", "santa-fe", "las-cruces", "roswell"],
    "texas": ["houston", "dallas", "austin", "san-antonio"],
    "california": ["los-angeles", "san-francisco", "san-diego", "sacramento"],
    "florida": ["miami", "orlando", "tampa", "jacksonville"],
    "new-york": ["new-york", "buffalo", "rochester", "albany"]
}

# Legal practice areas
PRACTICE_AREAS = [
    "car-accident",
    "business-litigation", 
    "personal-injury",
    "criminal-defense",
    "family-law",
    "real-estate",
    "employment-law",
    "immigration",
    "bankruptcy",
    "medical-malpractice"
]

# Crawl configuration
CRAWL_CONFIG = {
    "delay_between_requests": 2,  # seconds
    "max_retries": 3,
    "timeout": 30,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ],
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
}
