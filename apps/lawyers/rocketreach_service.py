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
            
            # Use the working /api/person/search endpoint
            # Add delay to avoid rate limiting
            time.sleep(1)
            response = self.session.post(f"{self.BASE_URL}/api/person/search", json=payload)
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
    
    def _determine_entity_type(self, lawyer_name: str, company_name: str = None) -> str:
        """
        Determine whether to search for a person or company based on available data
        
        Args:
            lawyer_name: Lawyer's name
            company_name: Company name
            
        Returns:
            'person' or 'company'
        """
        # If we have a specific lawyer name, search for person
        if lawyer_name and lawyer_name.strip() and lawyer_name != company_name:
            return 'person'
        
        # If we only have company name or lawyer name is same as company name, search for company
        if company_name and company_name.strip():
            return 'company'
        
        # Default to person search
        return 'person'
    
    def _clean_company_name(self, company_name: str) -> str:
        """
        Clean company name for better search results
        
        Args:
            company_name: Original company name
            
        Returns:
            Cleaned company name
        """
        if not company_name:
            return company_name
        
        # Remove common suffixes
        suffixes_to_remove = [
            ', P.A.', ', P.C.', ', PLLC', ', LLC', ', Inc.', ', Inc', 
            ', Corp.', ', Corporation', ', Ltd.', ', Limited',
            ', LLP', ', L.L.P.', ', L.L.C.', ', P.L.L.C.'
        ]
        
        cleaned_name = company_name.strip()
        for suffix in suffixes_to_remove:
            if cleaned_name.endswith(suffix):
                cleaned_name = cleaned_name[:-len(suffix)].strip()
                break
        
        return cleaned_name
    
    def find_lawyer_email(self, lawyer_name: str, company_name: str = None, 
                         domain: str = None, location: str = None) -> Optional[Dict]:
        """
        Find email for a lawyer using appropriate RocketReach API based on entity type
        
        Args:
            lawyer_name: Lawyer's name
            company_name: Law firm name
            domain: Company domain
            location: Location
            
        Returns:
            Dict with email and confidence score, or None if not found
        """
        try:
            # Determine entity type and choose appropriate API
            entity_type = self._determine_entity_type(lawyer_name, company_name)
            logger.info(f"Entity type determined: {entity_type} for {lawyer_name}")
            
            # Store raw API responses for debugging
            raw_responses = {}
            
            if entity_type == 'person':
                # Use person/search API
                search_results = self.search_person(
                    name=lawyer_name,
                    company=company_name,
                    domain=domain,
                    location=location
                )
                raw_responses['person_search'] = search_results
                logger.info(f"Person search results: {search_results}")
                
            elif entity_type == 'company':
                # Clean company name for better search results
                clean_company_name = self._clean_company_name(company_name)
                logger.info(f"Cleaned company name: {clean_company_name}")
                
                # Use company/search API to find company, then get employees
                # Don't use domain for company search as it may not match
                company_results = self.search_company(
                    name=clean_company_name,
                    domain=None,  # Don't use domain for company search
                    location=location
                )
                raw_responses['company_search'] = company_results
                logger.info(f"Company search results: {company_results}")
                
                # If company found, search for employees
                companies = company_results.get('companies', [])
                if companies:
                    company_id = companies[0].get('id')
                    logger.info(f"Found company with ID: {company_id}")
                    if company_id:
                        # Search for employees of this company
                        employee_results = self.search_company_employees(
                            company_name=company_name,
                            company_domain=None,  # Don't use domain for employee search
                            location=location
                        )
                        raw_responses['company_employees'] = employee_results
                        logger.info(f"Company employees results: {employee_results}")
                        
                        # Use employee results as search_results
                        search_results = employee_results
                    else:
                        search_results = company_results
                else:
                    search_results = company_results
            else:
                # Default to person search
                search_results = self.search_person(
                    name=lawyer_name,
                    company=company_name,
                    domain=domain,
                    location=location
                )
                raw_responses['person_search'] = search_results
                logger.info(f"Default person search results: {search_results}")
            
            # Process results based on API used
            profiles = []
            if search_results.get('profiles'):
                profiles = search_results.get('profiles', [])
            elif search_results.get('results'):
                profiles = search_results.get('results', [])
            elif search_results.get('data'):
                profiles = search_results.get('data', [])
            
            logger.info(f"Found {len(profiles)} profiles")
            
            if profiles:
                # Get the best match
                best_match = profiles[0]
                logger.info(f"Best match: {best_match}")
                
                # Extract information from API response
                # Store the original API response for debugging
                raw_response_data = search_results
                if 'company_employees' in raw_responses:
                    # Store the original company_employees API response
                    raw_response_data = raw_responses['company_employees']
                    logger.info(f"Using original company_employees API response: {type(raw_response_data)}")
                elif 'company_search' in raw_responses:
                    # Store the original company_search API response
                    raw_response_data = raw_responses['company_search']
                    logger.info(f"Using original company_search API response: {type(raw_response_data)}")
                else:
                    logger.info(f"Using search_results as raw_response: {type(raw_response_data)}")
                
                result = {
                    'rocketreach_id': best_match.get('id'),
                    'email': best_match.get('email'),
                    'phone': best_match.get('phone'),
                    'linkedin_url': best_match.get('linkedin_url'),
                    'twitter_url': best_match.get('twitter_url'),
                    'facebook_url': best_match.get('facebook_url'),
                    'current_title': best_match.get('current_title'),
                    'current_company': best_match.get('current_employer') or best_match.get('company'),
                    'location': best_match.get('location'),
                    'confidence_score': best_match.get('confidence_score', 0),
                    'raw_response': raw_response_data,  # Store full employee search results
                    'raw_data': raw_responses,  # Store all raw responses
                    # Additional professional data
                    'birth_year': best_match.get('birth_year'),
                    'job_history': best_match.get('job_history', []),
                    'education': best_match.get('education', []),
                    'skills': best_match.get('skills', []),
                    # Location coordinates
                        'region_latitude': best_match.get('region_latitude'),
                        'region_longitude': best_match.get('region_longitude'),
                        # Email and phone validation
                        'email_validation_status': best_match.get('email_validation_status', ''),
                        'phone_validation_status': best_match.get('phone_validation_status', '')
                    }
                return result
            else:
                # No profiles found, but still return raw data for debugging
                logger.info("No profiles found, returning raw data for debugging")
                
                # Use employee search results as raw_response if available
                raw_response_data = search_results
                if 'company_employees' in raw_responses:
                    raw_response_data = raw_responses['company_employees']
                
                return {
                    'rocketreach_id': None,
                    'email': None,
                    'phone': None,
                    'linkedin_url': None,
                    'twitter_url': None,
                    'facebook_url': None,
                    'current_title': None,
                    'current_company': None,
                    'location': None,
                    'confidence_score': 0,
                    'raw_response': raw_response_data,  # Store full employee search results
                    'raw_data': raw_responses,  # Store all raw responses
                    'birth_year': None,
                    'job_history': [],
                    'education': [],
                    'skills': [],
                    'region_latitude': None,
                    'region_longitude': None,
                    'email_validation_status': '',
                    'phone_validation_status': ''
                }
            
        except Exception as e:
            logger.error(f"Failed to find email for {lawyer_name}: {e}")
            return None
    
    def search_company(self, name: str = None, domain: str = None, industry: str = None, 
                       location: str = None, limit: int = 10) -> Dict:
        """
        Search for companies using RocketReach Company Search API
        
        Args:
            name: Company name
            domain: Company domain
            industry: Industry
            location: Location
            limit: Number of results to return
            
        Returns:
            Dict containing search results
        """
        try:
            query = {}
            
            if name:
                query["name"] = [name]
            if domain:
                query["domain"] = [domain]
            if industry:
                query["industry"] = [industry]
            if location:
                query["location"] = [location]
            
            payload = {
                "query": query,
                "limit": limit
            }
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            response = self.session.post("https://api.rocketreach.co/api/v2/searchCompany", json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to search company: {e}")
            raise

    def lookup_person_detailed(self, name: str, current_employer: str = None, 
                               location: str = None) -> Dict:
        """
        Lookup detailed person information using RocketReach Person Lookup API
        
        Args:
            name: Person's name
            current_employer: Current employer (required)
            location: Location
            
        Returns:
            Dict containing detailed person information
        """
        try:
            params = {
                "name": name
            }
            
            if current_employer:
                params["current_employer"] = current_employer
            if location:
                params["location"] = location
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            response = self.session.get("https://api.rocketreach.co/api/v2/person/lookup", params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to lookup person: {e}")
            raise

    def search_company_employees(self, company_name: str, company_domain: str = None, 
                                 location: str = None, limit: int = 10) -> Dict:
        """
        Search for employees of a specific company using People Search API
        
        Args:
            company_name: Company name
            company_domain: Company domain
            location: Location
            limit: Number of results to return
            
        Returns:
            Dict containing employee profiles
        """
        try:
            query = {
                "current_employer": [company_name]
            }
            
            if company_domain:
                query["current_employer_domain"] = [company_domain]
            if location:
                query["location"] = [location]
            
            payload = {
                "query": query,
                "limit": limit
            }
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            response = self.session.post(f"{self.BASE_URL}/api/person/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to search company employees: {e}")
            raise

    def get_employee_full_emails(self, company_name: str, employee_name: str, 
                                location: str = None) -> Dict:
        """
        Get full email addresses for a specific employee using Person Lookup API
        
        Args:
            company_name: Company name
            employee_name: Employee name
            location: Location
            
        Returns:
            Dict containing full employee information with emails
        """
        try:
            # First search for the employee
            search_result = self.search_company_employees(
                company_name=company_name,
                location=location,
                limit=1
            )
            
            if not search_result.get('profiles'):
                return {"error": "No employees found"}
            
            # Get the first matching employee
            employee = search_result['profiles'][0]
            
            # Use Person Lookup to get full details
            lookup_result = self.lookup_person_detailed(
                name=employee_name,
                current_employer=company_name,
                location=location
            )
            
            return lookup_result
            
        except Exception as e:
            logger.error(f"Failed to get employee full emails: {e}")
            return {"error": str(e)}

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
            # Use state instead of city for broader search
            location = lawyer.state if lawyer.state else f"{lawyer.city}, {lawyer.state}"
            result = self.api.find_lawyer_email(
                lawyer_name=lawyer.attorney_name or lawyer.company_name,
                company_name=lawyer.company_name,
                domain=lawyer.domain,
                location=location
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
                lookup.raw_data = result.get('raw_data', {})  # Store all raw API responses
                lookup.status = 'completed'
                lookup.api_credits_used = 1  # Assuming 1 credit per lookup
                
                # Additional professional data
                lookup.birth_year = result.get('birth_year')
                lookup.job_history = result.get('job_history', [])
                lookup.education = result.get('education', [])
                lookup.skills = result.get('skills', [])
                
                # Extract additional data from raw_data if available
                if lookup.raw_data and 'company_employees' in lookup.raw_data:
                    employee_data = lookup.raw_data['company_employees']
                    profiles = employee_data.get('profiles', [])
                    if profiles:
                        # Get the best match profile for additional data
                        best_profile = profiles[0]
                        
                        # Extract job history from profile
                        if not lookup.job_history and 'job_history' in best_profile:
                            lookup.job_history = best_profile.get('job_history', [])
                        
                        # Extract education from profile
                        if not lookup.education and 'education' in best_profile:
                            lookup.education = best_profile.get('education', [])
                        
                        # Extract skills from profile
                        if not lookup.skills and 'skills' in best_profile:
                            lookup.skills = best_profile.get('skills', [])
                        
                        # Extract all employee emails
                        employee_emails = []
                        for profile in profiles:
                            name = profile.get('name', 'N/A')
                            title = profile.get('current_title', 'N/A')
                            company = profile.get('current_employer', 'N/A')
                            
                            # Extract emails from teaser
                            teaser = profile.get('teaser', {})
                            emails = teaser.get('emails', [])
                            professional_emails = teaser.get('professional_emails', [])
                            
                            # Create email entries
                            for email_domain in emails:
                                employee_emails.append({
                                    'name': name,
                                    'title': title,
                                    'company': company,
                                    'email_domain': email_domain,
                                    'email_type': 'general',
                                    'source': 'rocketreach_teaser'
                                })
                            
                            for email_domain in professional_emails:
                                employee_emails.append({
                                    'name': name,
                                    'title': title,
                                    'company': company,
                                    'email_domain': email_domain,
                                    'email_type': 'professional',
                                    'source': 'rocketreach_professional'
                                })
                        
                        lookup.employee_emails = employee_emails
                
                # Location coordinates
                lookup.region_latitude = result.get('region_latitude')
                lookup.region_longitude = result.get('region_longitude')
                
                # Email and phone validation
                lookup.email_validation_status = result.get('email_validation_status', '')
                lookup.phone_validation_status = result.get('phone_validation_status', '')
                
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
