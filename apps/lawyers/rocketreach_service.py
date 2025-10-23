"""
RocketReach API service for email lookup
Based on: https://docs.rocketreach.co/reference/rocketreach-api
"""

import requests
import time
import logging
from typing import Dict, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class RocketReachAPI:
    """Service class for RocketReach API integration"""
    
    BASE_URL = "https://api.rocketreach.co/v2"
    
    def __init__(self, api_key: str = None):
        """
        Initialize RocketReach API client
        
        Args:
            api_key: RocketReach API key. If None, will use settings.ROCKETREACH_API_KEY
        """
        self.api_key = api_key or getattr(settings, 'ROCKETREACH_API_KEY', None)
        if not self.api_key:
            raise ValueError("RocketReach API key is required")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Api-Key': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def get_account_info(self) -> Dict:
        """Get account information and remaining credits"""
        try:
            # Try the correct endpoint for account info
            response = self.session.get(f"{self.BASE_URL}/account")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # If account endpoint fails, try to get info from a simple search
            try:
                # Use a simple search to test API key validity
                test_response = self.session.get(f"{self.BASE_URL}/person/search", params={'name': 'test'})
                if test_response.status_code == 200:
                    return {
                        'api_key_valid': True,
                        'message': 'API key is valid but account endpoint not available'
                    }
                else:
                    raise e
            except Exception as inner_e:
                logger.error(f"Failed to get account info: {e}")
                raise
    
    def search_person(self, name: str, company: str = None, domain: str = None, 
                     title: str = None, location: str = None) -> Dict:
        """
        Search for a person using RocketReach API with fallback
        
        Args:
            name: Person's name
            company: Company name
            domain: Company domain
            title: Job title
            location: Location
            
        Returns:
            Dict containing search results
        """
        # Try Universal People Search API first
        try:
            query = {
                "name": [name]
            }
            
            if company:
                query["current_employer"] = [company]
            if title:
                query["current_title"] = [title]
            if location:
                query["location"] = [location]
            
            payload = {
                "query": query
            }
            
            # Try Universal People Search endpoint
            response = self.session.post(f"{self.BASE_URL}/api/universal/person/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            if response.status_code == 403 and "Universal Credits" in response.text:
                logger.warning("Universal Credits required, falling back to regular API")
                # Fallback to regular API
                return self._search_person_regular(name, company, domain, title, location)
            else:
                logger.error(f"Failed to search person: {e}")
                raise
    
    def _search_person_regular(self, name: str, company: str = None, domain: str = None, 
                              title: str = None, location: str = None) -> Dict:
        """
        Fallback to regular person search API
        
        Args:
            name: Person's name
            company: Company name
            domain: Company domain
            title: Job title
            location: Location
            
        Returns:
            Dict containing search results
        """
        payload = {
            "name": name,
        }
        
        if company:
            payload["company"] = company
        if domain:
            payload["domain"] = domain
        if title:
            payload["title"] = title
        if location:
            payload["location"] = location
        
        try:
            response = self.session.post(f"{self.BASE_URL}/person/search", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to search person with regular API: {e}")
            raise
    
    def lookup_person(self, rocketreach_id: str) -> Dict:
        """
        Lookup person details by RocketReach ID
        
        Args:
            rocketreach_id: RocketReach person ID
            
        Returns:
            Dict containing person details
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/person/lookup/{rocketreach_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to lookup person {rocketreach_id}: {e}")
            raise
    
    def bulk_lookup_persons(self, person_ids: List[str]) -> Dict:
        """
        Bulk lookup multiple persons
        
        Args:
            person_ids: List of RocketReach person IDs
            
        Returns:
            Dict containing bulk lookup results
        """
        payload = {
            "person_ids": person_ids
        }
        
        try:
            response = self.session.post(f"{self.BASE_URL}/person/bulk_lookup", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to bulk lookup persons: {e}")
            raise
    
    def search_company(self, company_name: str, domain: str = None) -> Dict:
        """
        Search for company information
        
        Args:
            company_name: Company name
            domain: Company domain
            
        Returns:
            Dict containing company search results
        """
        payload = {
            "company": company_name
        }
        
        if domain:
            payload["domain"] = domain
        
        try:
            response = self.session.post(f"{self.BASE_URL}/company/search", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to search company: {e}")
            raise
    
    def lookup_company(self, company_id: str) -> Dict:
        """
        Lookup company details by ID
        
        Args:
            company_id: Company ID
            
        Returns:
            Dict containing company details
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/company/lookup/{company_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to lookup company {company_id}: {e}")
            raise
    
    def get_lookup_status(self, request_id: str) -> Dict:
        """
        Check status of a lookup request
        
        Args:
            request_id: Request ID from previous lookup
            
        Returns:
            Dict containing lookup status
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/person/lookup_status/{request_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get lookup status for {request_id}: {e}")
            raise
    
    def find_lawyer_email(self, lawyer_name: str, company_name: str = None, 
                         domain: str = None, location: str = None) -> Optional[Dict]:
        """
        Find email for a lawyer using Universal People Search API
        
        Args:
            lawyer_name: Lawyer's name
            company_name: Law firm name
            domain: Company domain
            location: Location
            
        Returns:
            Dict with email and confidence score, or None if not found
        """
        try:
            # Use Universal People Search API
            search_results = self.search_person(
                name=lawyer_name,
                company=company_name,
                domain=domain,
                location=location
            )
            
            # Universal API returns different structure
            if search_results.get('profiles') or search_results.get('results'):
                profiles = search_results.get('profiles', search_results.get('results', []))
                
                if profiles:
                    # Get the best match
                    best_match = profiles[0]
                    
                    # Extract information from Universal API response
                    return {
                        'rocketreach_id': best_match.get('id'),
                        'email': best_match.get('email'),
                        'phone': best_match.get('phone'),
                        'linkedin_url': best_match.get('linkedin_url'),
                        'twitter_url': best_match.get('twitter_url'),
                        'facebook_url': best_match.get('facebook_url'),
                        'current_title': best_match.get('current_title'),
                        'current_company': best_match.get('current_employer'),
                        'location': best_match.get('location'),
                        'confidence_score': best_match.get('confidence_score', 0),
                        'raw_response': best_match
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find email for {lawyer_name}: {e}")
            return None
    
    def get_remaining_credits(self) -> int:
        """Get remaining API credits"""
        try:
            account_info = self.get_account_info()
            return account_info.get('credits_remaining', 0)
        except Exception as e:
            logger.error(f"Failed to get remaining credits: {e}")
            return 0
    
    def is_rate_limited(self) -> bool:
        """Check if we're being rate limited"""
        try:
            account_info = self.get_account_info()
            return account_info.get('rate_limited', False)
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False


class RocketReachLookupService:
    """Service class for managing RocketReach lookups in the database"""
    
    def __init__(self, api_key: str = None):
        self.api = RocketReachAPI(api_key)
    
    def lookup_lawyer_email(self, lawyer, force_refresh: bool = False) -> Optional[Dict]:
        """
        Lookup email for a lawyer and save results to database
        
        Args:
            lawyer: Lawyer model instance
            force_refresh: Force new lookup even if previous exists
            
        Returns:
            RocketReachLookup instance or None
        """
        from apps.lawyers.models import RocketReachLookup
        
        # Check if we already have a successful lookup
        if not force_refresh:
            existing_lookup = RocketReachLookup.objects.filter(
                lawyer=lawyer,
                status='completed',
                email__isnull=False
            ).first()
            
            if existing_lookup:
                return existing_lookup
        
        # Create new lookup record
        lookup = RocketReachLookup.objects.create(
            lawyer=lawyer,
            lookup_name=lawyer.attorney_name or lawyer.company_name,
            lookup_company=lawyer.company_name,
            lookup_domain=lawyer.domain,
            status='processing'
        )
        
        try:
            # Perform API lookup
            result = self.api.find_lawyer_email(
                lawyer_name=lawyer.attorney_name or lawyer.company_name,
                company_name=lawyer.company_name,
                domain=lawyer.domain,
                location=f"{lawyer.city}, {lawyer.state}"
            )
            
            if result:
                # Update lookup with results
                lookup.rocketreach_id = result.get('rocketreach_id', '')
                lookup.email = result.get('email', '')
                lookup.phone = result.get('phone', '')
                lookup.linkedin_url = result.get('linkedin_url', '')
                lookup.twitter_url = result.get('twitter_url', '')
                lookup.facebook_url = result.get('facebook_url', '')
                lookup.current_title = result.get('current_title', '')
                lookup.current_company = result.get('current_company', '')
                lookup.location = result.get('location', '')
                lookup.confidence_score = result.get('confidence_score', 0)
                lookup.raw_response = result.get('raw_response', {})
                lookup.status = 'completed'
                lookup.api_credits_used = 1  # Assuming 1 credit per lookup
                
                # Update lawyer's email if found
                if lookup.email:
                    lookup.update_lawyer_email()
                
            else:
                lookup.status = 'not_found'
            
            lookup.save()
            return lookup
            
        except Exception as e:
            logger.error(f"Failed to lookup email for {lawyer.company_name}: {e}")
            lookup.status = 'failed'
            lookup.save()
            return None
    
    def bulk_lookup_lawyers(self, lawyers, batch_size: int = 10) -> List[Dict]:
        """
        Bulk lookup emails for multiple lawyers
        
        Args:
            lawyers: QuerySet or list of Lawyer instances
            batch_size: Number of lawyers to process in each batch
            
        Returns:
            List of lookup results
        """
        results = []
        
        for i in range(0, len(lawyers), batch_size):
            batch = lawyers[i:i + batch_size]
            
            for lawyer in batch:
                try:
                    result = self.lookup_lawyer_email(lawyer)
                    results.append({
                        'lawyer_id': lawyer.id,
                        'lawyer_name': lawyer.company_name,
                        'success': result is not None and result.is_successful(),
                        'email': result.email if result else None,
                        'confidence': result.confidence_score if result else 0
                    })
                    
                    # Add delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to lookup {lawyer.company_name}: {e}")
                    results.append({
                        'lawyer_id': lawyer.id,
                        'lawyer_name': lawyer.company_name,
                        'success': False,
                        'error': str(e)
                    })
        
        return results
