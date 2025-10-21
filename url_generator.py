"""
S1: Generate StartURLs - Create URL list for crawling
"""

import itertools
from typing import List, Dict
from config import LAW_DOMAINS, STATES_CITIES, PRACTICE_AREAS


class URLGenerator:
    """Generate URLs for lawyer data crawling"""
    
    def __init__(self):
        self.domains = LAW_DOMAINS
        self.states_cities = STATES_CITIES
        self.practice_areas = PRACTICE_AREAS
    
    def generate_urls(self) -> List[Dict]:
        """Generate URLs for all combinations of domains, practice areas, states, cities"""
        urls = []
        
        for domain_name, domain_config in self.domains.items():
            for state, cities in self.states_cities.items():
                for city in cities:
                    for practice_area in self.practice_areas:
                        url = self._build_url(domain_config, practice_area, state, city)
                        urls.append({
                            "domain": domain_name,
                            "url": url,
                            "practice_area": practice_area,
                            "state": state,
                            "city": city,
                            "selectors": domain_config["selectors"]
                        })
        
        return urls
    
    def _build_url(self, domain_config: Dict, practice_area: str, state: str, city: str) -> str:
        """Build URL according to domain pattern"""
        url_pattern = domain_config["url_pattern"]
        base_url = domain_config["base_url"]
        
        return url_pattern.format(
            base_url=base_url,
            practice_area=practice_area,
            state=state,
            city=city
        )
    
    def generate_urls_for_domain(self, domain_name: str) -> List[Dict]:
        """Generate URLs for specific domain"""
        if domain_name not in self.domains:
            raise ValueError(f"Domain '{domain_name}' not found")
        
        urls = []
        domain_config = self.domains[domain_name]
        
        for state, cities in self.states_cities.items():
            for city in cities:
                for practice_area in self.practice_areas:
                    url = self._build_url(domain_config, practice_area, state, city)
                    urls.append({
                        "domain": domain_name,
                        "url": url,
                        "practice_area": practice_area,
                        "state": state,
                        "city": city,
                        "selectors": domain_config["selectors"]
                    })
        
        return urls
    
    def generate_urls_for_state(self, state: str) -> List[Dict]:
        """Generate URLs for specific state"""
        if state not in self.states_cities:
            raise ValueError(f"State '{state}' not found")
        
        urls = []
        cities = self.states_cities[state]
        
        for domain_name, domain_config in self.domains.items():
            for city in cities:
                for practice_area in self.practice_areas:
                    url = self._build_url(domain_config, practice_area, state, city)
                    urls.append({
                        "domain": domain_name,
                        "url": url,
                        "practice_area": practice_area,
                        "state": state,
                        "city": city,
                        "selectors": domain_config["selectors"]
                    })
        
        return urls
    
    def get_total_urls_count(self) -> int:
        """Calculate total number of URLs to be generated"""
        total_domains = len(self.domains)
        total_states = len(self.states_cities)
        total_cities = sum(len(cities) for cities in self.states_cities.values())
        total_practice_areas = len(self.practice_areas)
        
        return total_domains * total_cities * total_practice_areas


if __name__ == "__main__":
    generator = URLGenerator()
    
    print(f"Total URLs to be generated: {generator.get_total_urls_count()}")
    
    sample_urls = generator.generate_urls()[:5]
    print("\nSample URLs:")
    for url_info in sample_urls:
        print(f"- {url_info['domain']}: {url_info['url']}")
        print(f"  Practice: {url_info['practice_area']}, State: {url_info['state']}, City: {url_info['city']}")
        print()
