import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Handles rate limiting for RocketReach API"""
    
    RATE_LIMITS = {
        'person_search': {
            'per_minute': 15,
            'per_hour': 50,
            'per_day': 500,
            'per_month': 10000
        },
        'person_lookup': {
            'per_minute': 15,
            'per_hour': 100,
            'per_day': 500,
            'per_month': 5000
        },
        'global': {
            'per_second': 10  # Global limit across all APIs
        }
    }
    
    def __init__(self):
        self.last_request_time = 0
        self.request_count_minute = 0
        self.request_count_hour = 0
        self.minute_start_time = time.time()
        self.hour_start_time = time.time()
    
    def check_and_enforce_limits(self, api_type: str) -> None:
        """Check and enforce rate limits before making request"""
        current_time = time.time()
        
        # Reset counters if time windows have passed
        self._reset_counters_if_needed(current_time)
        
        # Check global per-second limit
        self._enforce_global_rate_limit(current_time)
        
        # Check per-minute and per-hour limits
        self._enforce_api_specific_limits(api_type, current_time)
        
        # Update counters
        self._update_counters(current_time)
    
    def _reset_counters_if_needed(self, current_time: float) -> None:
        """Reset counters if time windows have passed"""
        if current_time - self.minute_start_time >= 60:
            self.request_count_minute = 0
            self.minute_start_time = current_time
        
        if current_time - self.hour_start_time >= 3600:
            self.request_count_hour = 0
            self.hour_start_time = current_time
    
    def _enforce_global_rate_limit(self, current_time: float) -> None:
        """Enforce global per-second rate limit"""
        if current_time - self.last_request_time < 0.1:  # 100ms between requests
            sleep_time = 0.1 - (current_time - self.last_request_time)
            logger.info(f"Global rate limit: sleeping {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
    
    def _enforce_api_specific_limits(self, api_type: str, current_time: float) -> None:
        """Enforce API-specific rate limits"""
        limits = self.RATE_LIMITS.get(api_type, {})
        
        # Check per-minute limit
        if self.request_count_minute >= limits.get('per_minute', 15):
            sleep_time = 60 - (current_time - self.minute_start_time)
            if sleep_time > 0:
                logger.warning(f"Per-minute rate limit reached. Sleeping {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count_minute = 0
                self.minute_start_time = time.time()
        
        # Check per-hour limit
        if self.request_count_hour >= limits.get('per_hour', 50):
            sleep_time = 3600 - (current_time - self.hour_start_time)
            if sleep_time > 0:
                logger.warning(f"Per-hour rate limit reached. Sleeping {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count_hour = 0
                self.hour_start_time = time.time()
    
    def _update_counters(self, current_time: float) -> None:
        """Update request counters"""
        self.request_count_minute += 1
        self.request_count_hour += 1
        self.last_request_time = current_time
    
    def get_status(self) -> Dict:
        """Get current rate limit status"""
        current_time = time.time()
        
        return {
            "requests_this_minute": self.request_count_minute,
            "requests_this_hour": self.request_count_hour,
            "minute_limit": self.RATE_LIMITS['person_search']['per_minute'],
            "hour_limit": self.RATE_LIMITS['person_search']['per_hour'],
            "time_since_last_request": current_time - self.last_request_time,
            "minute_reset_in": max(0, 60 - (current_time - self.minute_start_time)),
            "hour_reset_in": max(0, 3600 - (current_time - self.hour_start_time))
        }


class APIErrorHandler:
    """Handles API errors and responses"""
    
    @staticmethod
    def handle_rate_limit(response: requests.Response) -> int:
        """Handle rate limit response and return retry delay"""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            logger.warning(f"Rate limit exceeded. Retry-After: {retry_after} seconds")
            return retry_after
        return 0
    
    @staticmethod
    def handle_api_error(response: requests.Response) -> None:
        """Handle API errors according to RocketReach documentation"""
        if response.status_code == 400:
            logger.error(f"Bad Request (400): {response.text}")
            raise requests.exceptions.HTTPError(f"Bad Request: {response.text}")
        elif response.status_code == 401:
            logger.error(f"Unauthorized (401): Invalid API Key")
            raise requests.exceptions.HTTPError("Unauthorized: Invalid API Key")
        elif response.status_code == 403:
            logger.error(f"Forbidden (403): API Key lacks permission")
            raise requests.exceptions.HTTPError("Forbidden: API Key lacks permission")
        elif response.status_code == 404:
            logger.warning(f"Not Found (404): Resource does not exist")
            # Don't raise error for 404, just log warning
        elif response.status_code == 500:
            logger.error(f"Internal Server Error (500): {response.text}")
            raise requests.exceptions.HTTPError(f"Internal Server Error: {response.text}")


class RocketReachAPI:
    """RocketReach API client with rate limiting"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.BASE_URL = "https://api.rocketreach.co/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        })
        
        # Initialize rate limiter and error handler
        self.rate_limiter = RateLimiter()
        self.error_handler = APIErrorHandler()
    
    def _check_rate_limits(self, api_type: str) -> None:
        """Check and enforce rate limits before making request"""
        self.rate_limiter.check_and_enforce_limits(api_type)
    
    def _handle_rate_limit(self, response: requests.Response) -> int:
        """Handle rate limit response and return retry delay"""
        return self.error_handler.handle_rate_limit(response)
    
    def _handle_api_error(self, response: requests.Response) -> None:
        """Handle API errors according to RocketReach documentation"""
        self.error_handler.handle_api_error(response)
    
    def search_person(self, name: str = None, company: str = None, 
                     domain: str = None, title: str = None, location: str = None) -> Dict:
        """
        Search for a person using the People Search API
        
        Args:
            name: Person's name
            company: Company name
            domain: Company domain
            title: Job title
            location: Location
            
        Returns:
            Dict containing search results
        """
        payload = self._build_search_payload(name, company, domain, title, location)
        
        try:
            response = self._make_search_request(payload)
            return self._process_search_response(response)
            
        except requests.RequestException as e:
            logger.error(f"Failed to search person: {e}")
            raise
    
    def _build_search_payload(self, name: str, company: str, domain: str, 
                            title: str, location: str) -> Dict:
        """Build search payload for person search API"""
        payload = {
            "query": {
                "name": [name] if name else [],
                "current_employer": [company] if company else []
            },
            "page_size": 20,  # Get more results
            "start": 1
        }
        
        # Add law-related keywords to broaden search
        if company:
            law_keywords = ['law', 'attorney', 'lawyer', 'legal', 'law firm', 'law office']
            payload["query"]["current_employer"].extend([f"{company} {kw}" for kw in law_keywords[:2]])
        
        return payload
    
    def _make_search_request(self, payload: Dict) -> requests.Response:
        """Make the actual search request with rate limiting and retry logic"""
        # Check and enforce rate limits before making request
        self._check_rate_limits('person_search')
        
        # Use the People Search API endpoint
        response = self.session.post(f"{self.BASE_URL}/person/search", json=payload)
        
        # Check for rate limit first
        retry_delay = self._handle_rate_limit(response)
        if retry_delay > 0:
            logger.warning(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            # Retry once
            response = self.session.post(f"{self.BASE_URL}/person/search", json=payload)
        
        return response
    
    def _process_search_response(self, response: requests.Response) -> Dict:
        """Process the search response and handle errors"""
        logger.debug(f"Search response status: {response.status_code}")
        logger.debug(f"Search response headers: {dict(response.headers)}")
        
        # Handle other API errors
        self._handle_api_error(response)
        
        # If we get here, response should be successful
        if response.status_code in [200, 201]:  # Both 200 and 201 are success codes
            try:
                data = response.json()
                logger.debug(f"Search response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                return data
            except Exception as e:
                logger.error(f"Failed to parse search response JSON: {e}")
                logger.error(f"Response text: {response.text[:500]}")
                return {"profiles": [], "pagination": {"total": 0}}
        else:
            # Handle 404 as valid case (no results found)
            if response.status_code == 404:
                logger.info("Search returned 404 - no results found")
                return {"profiles": [], "pagination": {"total": 0}}
            else:
                logger.error(f"Unexpected status code: {response.status_code}")
                logger.error(f"Response text: {response.text[:500]}")
                response.raise_for_status()
    
    def lookup_person(self, person_id: int = None, name: str = None, 
                     current_employer: str = None, email: str = None, 
                     linkedin_url: str = None, title: str = None,
                     lookup_type: str = 'standard') -> Dict:
        """
        Lookup a person using the People Lookup API
        
        Args:
            person_id: RocketReach person ID
            name: Name of the person (must specify along with current_employer)
            current_employer: Current employer (must specify along with name)
            email: Email address for lookup
            linkedin_url: LinkedIn URL for lookup
            title: Job title of the person
            lookup_type: Type of lookup (standard, premium, bulk, phone, enrich)
            
        Returns:
            Dict containing lookup results with full email
        """
        params = {}
        
        # Build parameters based on what's provided
        if person_id:
            params['id'] = person_id
        elif name and current_employer:
            params['name'] = name
            params['current_employer'] = current_employer
        elif email:
            params['email'] = email
        elif linkedin_url:
            params['linkedin_url'] = linkedin_url
        else:
            raise ValueError("Must provide either person_id, (name + current_employer), email, or linkedin_url")
        
        # Add optional parameters
        if title:
            params['title'] = title
        if lookup_type:
            params['lookup_type'] = lookup_type
        
        try:
            response = self._make_lookup_request(params)
            return self._process_lookup_response(response)
            
        except requests.RequestException as e:
            logger.error(f"Failed to lookup person: {e}")
            raise
    
    def _make_lookup_request(self, params: Dict) -> requests.Response:
        """Make the actual lookup request with rate limiting and retry logic"""
        # Check and enforce rate limits before making request
        self._check_rate_limits('person_lookup')
        
        # Use the People Lookup API endpoint
        response = self.session.get(f"{self.BASE_URL}/person/lookup", params=params)
        
        # Check for rate limit first
        retry_delay = self._handle_rate_limit(response)
        if retry_delay > 0:
            logger.warning(f"Rate limit exceeded for person lookup. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            # Retry once
            response = self.session.get(f"{self.BASE_URL}/person/lookup", params=params)
        
        return response
    
    def _process_lookup_response(self, response: requests.Response) -> Dict:
        """Process the lookup response and handle errors"""
        # Handle other API errors
        self._handle_api_error(response)
        
        # If we get here, response should be successful
        if response.status_code in [200, 201]:  # Both 200 and 201 are success codes
            return response.json()
        else:
            # Handle 404 as valid case (person not found)
            if response.status_code == 404:
                return {"emails": [], "status": "not_found"}
            else:
                response.raise_for_status()
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        return self.rate_limiter.get_status()
    
    def check_lookup_status(self, profile_ids: List[int]) -> Dict:
        """
        Check the status of person lookup requests
        
        Args:
            profile_ids: List of profile IDs to check status for
            
        Returns:
            Dict containing status information
        """
        try:
            params = {'ids': profile_ids}
            response = self.session.get(f"{self.BASE_URL}/person/checkStatus", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed with status {response.status_code}"}
        except requests.RequestException as e:
            logger.warning(f"Could not check lookup status: {e}")
            return {"error": str(e)}
    
    def check_api_usage(self) -> Dict:
        """Check API usage and limits (if available)"""
        try:
            # This endpoint might not exist, but we can try
            response = self.session.get(f"{self.BASE_URL}/usage")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Usage endpoint not available"}
        except requests.RequestException as e:
            logger.warning(f"Could not check API usage: {e}")
            return {"error": str(e)}


class EmailProcessor:
    """Handles email processing and validation logic"""
    
    @staticmethod
    def extract_emails_from_lookup(lookup_result: Dict) -> List[Dict]:
        """Extract and process emails from person lookup result"""
        emails_data = lookup_result.get('emails', [])
        actual_emails = []
        
        if emails_data:
            for email_info in emails_data:
                email = email_info.get('email')
                email_type = email_info.get('type', 'unknown')
                grade = email_info.get('grade', 'unknown')
                smtp_valid = email_info.get('smtp_valid', 'unknown')
                
                if email:
                    actual_emails.append({
                        'email': email,
                        'type': email_type,
                        'grade': grade,
                        'smtp_valid': smtp_valid
                    })
        
        return actual_emails
    
    @staticmethod
    def find_best_email(employee_emails: List[Dict]) -> Optional[str]:
        """Find the best email from employee emails list"""
        for emp in employee_emails:
            actual_emails = emp.get('actual_emails', [])
            if actual_emails:
                # Find the best email (professional, high grade, valid)
                for email_info in actual_emails:
                    if (email_info.get('type') == 'professional' and 
                        email_info.get('grade') in ['A', 'A-', 'B+', 'B'] and
                        email_info.get('smtp_valid') == 'valid'):
                        return email_info['email']
                
                # If no professional email found, use any valid email
                for email_info in actual_emails:
                    if email_info.get('smtp_valid') == 'valid':
                        return email_info['email']
                
                # If still no valid email, use the first email
                if actual_emails:
                    return actual_emails[0]['email']
        
        return None


class NameVariationGenerator:
    """Generates name variations for search"""
    
    @staticmethod
    def generate_name_variations(lawyer_name: str) -> List[str]:
        """Generate different name variations for search"""
        name_variations = []
        
        if lawyer_name:
            name_parts = lawyer_name.split()
            if len(name_parts) >= 2:
                # Full name
                name_variations.append(lawyer_name)
                # First name only
                name_variations.append(name_parts[0])
                # First + Last name (remove middle initial)
                if len(name_parts) >= 2:
                    name_variations.append(f"{name_parts[0]} {name_parts[-1]}")
                # Last name only
                name_variations.append(name_parts[-1])
            else:
                name_variations.append(lawyer_name)
        else:
            # If no lawyer name, try common lawyer titles
            name_variations = ['Attorney', 'Lawyer', 'Partner']
        
        return name_variations


class ProfileFilter:
    """Filters profiles for law-related content"""
    
    LAW_KEYWORDS = ['attorney', 'lawyer', 'legal', 'law', 'counsel', 'partner', 'associate']
    
    @staticmethod
    def filter_law_profiles(profiles: List[Dict]) -> List[Dict]:
        """Filter profiles to only include law-related ones"""
        law_profiles = []
        
        for profile in profiles:
            title = profile.get('current_title', '').lower()
            employer = profile.get('current_employer', '').lower()
            
            # Check if it's law-related
            is_law_related = any(keyword in title for keyword in ProfileFilter.LAW_KEYWORDS) or \
                           any(keyword in employer for keyword in ProfileFilter.LAW_KEYWORDS)
            
            if is_law_related:
                law_profiles.append(profile)
        
        return law_profiles


class ResultBuilder:
    """Builds result objects for API responses"""
    
    @staticmethod
    def build_success_result(best_match: Dict, best_email: str, 
                           raw_response_data: Dict, raw_responses: Dict, 
                           employee_emails: List[Dict]) -> Dict:
        """Build success result object"""
        return {
            'success': True,
            'status': 'found',
            'rocketreach_id': best_match.get('id'),
            'email': best_email,
            'phone': best_match.get('phone'),
            'linkedin_url': best_match.get('linkedin_url'),
            'twitter_url': best_match.get('twitter_url'),
            'facebook_url': best_match.get('facebook_url'),
            'current_title': best_match.get('current_title'),
            'current_company': best_match.get('current_employer'),
            'location': best_match.get('location'),
            'confidence_score': 0.5,
            'raw_response': raw_response_data,
            'raw_data': raw_responses,
            'employee_emails': employee_emails,
            'birth_year': best_match.get('birth_year'),
            'job_history': best_match.get('job_history', []),
            'education': best_match.get('education', []),
            'skills': best_match.get('skills', []),
            'region_latitude': best_match.get('region_latitude'),
            'region_longitude': best_match.get('region_longitude'),
            'email_validation_status': best_match.get('email_validation_status', ''),
            'phone_validation_status': best_match.get('phone_validation_status', '')
        }
    
    @staticmethod
    def build_not_found_result(raw_response_data: Dict, raw_responses: Dict, 
                             employee_emails: List[Dict]) -> Dict:
        """Build not found result object"""
        return {
            'success': False,
            'status': 'not_found',
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
            'raw_response': raw_response_data,
            'raw_data': raw_responses,
            'employee_emails': employee_emails,
            'birth_year': None,
            'job_history': [],
            'education': [],
            'skills': [],
            'region_latitude': None,
            'region_longitude': None,
            'email_validation_status': '',
            'phone_validation_status': ''
        }
    
    @staticmethod
    def build_error_result(error_message: str) -> Dict:
        """Build error result object"""
        return {
            'success': False,
            'status': 'failed',
            'error': error_message,
            'raw_response': {},
            'raw_data': {},
            'employee_emails': []
        }


class RocketReachLookupService:
    """Service for looking up lawyer emails using RocketReach API"""
    
    def __init__(self, api_key: str):
        self.api = RocketReachAPI(api_key)
        self.email_processor = EmailProcessor()
        self.name_generator = NameVariationGenerator()
        self.profile_filter = ProfileFilter()
        self.result_builder = ResultBuilder()
    
    def find_lawyer_email(self, lawyer_name: str, company_name: str = None, 
                         domain: str = None, location: str = None) -> Optional[Dict]:
        """
        Find lawyer email using RocketReach API
        
        Args:
            lawyer_name: Lawyer's name
            company_name: Company name
            domain: Company domain
            location: Location
            
        Returns:
            Dict containing email information or None if not found
        """
        try:
            logger.info(f"Searching for lawyer: {lawyer_name} at company: {company_name}")
            
            # Search for profiles using name variations
            search_results, raw_responses = self._search_with_name_variations(
                lawyer_name, company_name, location
            )
            
            # Process search results
            profiles = self._extract_profiles_from_search(search_results)
            logger.info(f"Found {len(profiles)} profiles")
            
            # Process profiles to get employee emails
            best_match, employee_emails = self._process_profiles_for_emails(
                profiles, raw_responses
            )
            
            # Build and return result
            return self._build_final_result(
                best_match, employee_emails, search_results, raw_responses
            )
            
        except Exception as e:
            logger.error(f"Failed to find email for {company_name or lawyer_name}: {e}")
            return self.result_builder.build_error_result(str(e))
    
    def _search_with_name_variations(self, lawyer_name: str, company_name: str, 
                                   location: str) -> Tuple[Dict, Dict]:
        """Search for profiles using different name variations"""
        raw_responses = {}
        search_results = None
        
        # Generate name variations
        name_variations = self.name_generator.generate_name_variations(lawyer_name)
        if not lawyer_name and company_name:
            name_variations.append(company_name)
        
        # Try each name variation
        for name_var in name_variations:
            try:
                logger.info(f"Trying name variation: '{name_var}'")
                search_results = self.api.search_person(
                    name=name_var,
                    company=company_name,
                    location=location
                )
                raw_responses[f'person_search_{name_var}'] = search_results
                
                if search_results is None:
                    logger.warning(f"Search returned None for '{name_var}'")
                    continue
                
                # Filter for law-related profiles
                profiles = search_results.get('profiles', [])
                if profiles:
                    law_profiles = self.profile_filter.filter_law_profiles(profiles)
                    if law_profiles:
                        logger.info(f"Found {len(law_profiles)} law-related profiles with name '{name_var}'")
                        search_results['profiles'] = law_profiles
                        break
                    else:
                        logger.info(f"Found {len(profiles)} profiles but none are law-related with name '{name_var}'")
                else:
                    logger.info(f"No profiles found with name '{name_var}'")
                    
            except Exception as e:
                logger.warning(f"Failed to search with name '{name_var}': {e}")
                continue
        
        # Use the last search results (most comprehensive)
        if not search_results:
            search_results = {'profiles': [], 'pagination': {'total': 0}}
            raw_responses['person_search'] = search_results
        
        logger.info(f"Final person search results: {search_results}")
        return search_results, raw_responses
    
    def _extract_profiles_from_search(self, search_results: Dict) -> List[Dict]:
        """Extract profiles from search results"""
        profiles = search_results.get('profiles', [])
        if not profiles:
            # Fallback to 'people' if 'profiles' is empty (new format)
            profiles = search_results.get('people', [])
        return profiles
    
    def _process_profiles_for_emails(self, profiles: List[Dict], 
                                   raw_responses: Dict) -> Tuple[Optional[Dict], List[Dict]]:
        """Process profiles to extract email information"""
        best_match = None
        employee_emails = []
        
        if profiles:
            best_match = profiles[0]
            logger.info(f"Best match: {best_match}")
        
        # Process all profiles with 2-step lookup
        for i, profile in enumerate(profiles):
            name = profile.get('name', 'N/A')
            title = profile.get('current_title', 'N/A')
            company = profile.get('current_employer', 'N/A')
            current_employer_domain = profile.get('current_employer_domain', '')
            person_id = profile.get('id')
            
            logger.info(f"Profile {i+1}: {name} - {title} at {company} (domain: {current_employer_domain}, ID: {person_id})")
            
            # Step 2: Use person/lookup to get full email
            actual_emails = self._lookup_person_emails(person_id, name, raw_responses, title, company)
            
            # Store profile as employee email
            employee_emails.append({
                'name': name,
                'title': title,
                'company': company,
                'email_domain': current_employer_domain,
                'email_type': 'current_company',
                'source': 'person_lookup' if actual_emails else 'no_data',
                'confidence': 'high' if actual_emails else 'low',
                'actual_emails': actual_emails,
                'match_score': 0.5
            })
        
        return best_match, employee_emails
    
    def _lookup_person_emails(self, person_id: int, name: str, 
                            raw_responses: Dict, title: str = None, 
                            company: str = None) -> List[Dict]:
        """Lookup person emails using person ID or name+company"""
        actual_emails = []
        
        if person_id:
            try:
                logger.info(f"Looking up person ID {person_id} for full email...")
                lookup_result = self.api.lookup_person(person_id=person_id)
                raw_responses[f'person_lookup_{person_id}'] = lookup_result
                
                # Extract emails from lookup result
                actual_emails = self.email_processor.extract_emails_from_lookup(lookup_result)
                
                if actual_emails:
                    logger.info(f"Found {len(actual_emails)} emails for {name}")
                    for email_info in actual_emails:
                        logger.info(f"Found email for {name}: {email_info['email']} "
                                  f"(type: {email_info['type']}, grade: {email_info['grade']}, "
                                  f"valid: {email_info['smtp_valid']})")
                else:
                    logger.info(f"No emails found in lookup for {name}")
                    
            except Exception as e:
                logger.warning(f"Failed to lookup person {person_id}: {e}")
        elif name and company:
            try:
                logger.info(f"Looking up {name} at {company} for full email...")
                lookup_result = self.api.lookup_person(
                    name=name, 
                    current_employer=company,
                    title=title
                )
                raw_responses[f'person_lookup_{name}_{company}'] = lookup_result
                
                # Extract emails from lookup result
                actual_emails = self.email_processor.extract_emails_from_lookup(lookup_result)
                
                if actual_emails:
                    logger.info(f"Found {len(actual_emails)} emails for {name}")
                    for email_info in actual_emails:
                        logger.info(f"Found email for {name}: {email_info['email']} "
                                  f"(type: {email_info['type']}, grade: {email_info['grade']}, "
                                  f"valid: {email_info['smtp_valid']})")
                else:
                    logger.info(f"No emails found in lookup for {name}")
                    
            except Exception as e:
                logger.warning(f"Failed to lookup person {name} at {company}: {e}")
        
        return actual_emails
    
    def _build_final_result(self, best_match: Optional[Dict], employee_emails: List[Dict],
                          search_results: Dict, raw_responses: Dict) -> Dict:
        """Build the final result object"""
        raw_response_data = search_results
        
        if best_match:
            # Find the best email from employee emails
            best_email = self.email_processor.find_best_email(employee_emails)
            
            if best_email:
                logger.info(f"Using best email: {best_email}")
            else:
                logger.info("No valid email found")
            
            return self.result_builder.build_success_result(
                best_match, best_email, raw_response_data, raw_responses, employee_emails
            )
        else:
            # No profiles found
            return self.result_builder.build_not_found_result(
                raw_response_data, raw_responses, employee_emails
            )
    
    def lookup_lawyer_email(self, lawyer_id: int, force_refresh: bool = False) -> Dict:
        """
        Lookup email for a specific lawyer
        
        Args:
            lawyer_id: Lawyer ID
            force_refresh: Force refresh even if already looked up
            
        Returns:
            Dict containing lookup results
        """
        from .models import Lawyer, RocketReachLookup
        
        try:
            lawyer = Lawyer.objects.get(id=lawyer_id)
            
            # Check if already looked up (unless force refresh)
            if not force_refresh:
                existing_lookup = self._get_existing_lookup(lawyer)
                if existing_lookup:
                    return self._build_existing_lookup_result(lawyer, existing_lookup)
            
            # Create new lookup record and process
            lookup = self._create_lookup_record(lawyer)
            result = self._find_lawyer_email_with_retry(lawyer)
            
            # Update lookup with results
            self._update_lookup_with_result(lookup, result)
            
            return self._build_lookup_result(lawyer, result, lookup)
                
        except Lawyer.DoesNotExist:
            logger.error(f"Lawyer with ID {lawyer_id} not found")
            return {
                'success': False,
                'error': 'Lawyer not found',
                'lawyer_id': lawyer_id
            }
        except Exception as e:
            logger.error(f"Failed to lookup email for lawyer {lawyer_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'lawyer_id': lawyer_id
            }
    
    def _get_existing_lookup(self, lawyer) -> Optional[object]:
        """Get existing lookup if available"""
        from .models import RocketReachLookup
        
        return RocketReachLookup.objects.filter(
            lawyer=lawyer,
            status__in=['completed', 'found']
        ).first()
    
    def _build_existing_lookup_result(self, lawyer, existing_lookup) -> Dict:
        """Build result for existing lookup"""
        logger.info(f"Lawyer {lawyer.id} already looked up, returning existing result")
        return {
            'success': True,
            'lawyer_id': lawyer.id,
            'lawyer_name': lawyer.attorney_name or lawyer.company_name,
            'email': existing_lookup.email,
            'confidence': existing_lookup.confidence_score,
            'status': existing_lookup.status,
            'lookup_id': existing_lookup.id
        }
    
    def _create_lookup_record(self, lawyer) -> object:
        """Create new lookup record"""
        from .models import RocketReachLookup
        
        return RocketReachLookup.objects.create(
            lawyer=lawyer,
            status='in_progress'
        )
    
    def _find_lawyer_email_with_retry(self, lawyer) -> Dict:
        """Find lawyer email with retry logic"""
        return self.find_lawyer_email(
            lawyer_name=lawyer.attorney_name,
            company_name=lawyer.company_name,
            domain=lawyer.domain,
            location=lawyer.state
        )
    
    def _update_lookup_with_result(self, lookup, result) -> None:
        """Update lookup record with search results"""
        if result and result.get('success') is not False:
            # Update lookup with results
            lookup.rocketreach_id = result.get('rocketreach_id')
            lookup.email = result.get('email')
            lookup.phone = result.get('phone')
            lookup.linkedin_url = result.get('linkedin_url')
            lookup.twitter_url = result.get('twitter_url')
            lookup.facebook_url = result.get('facebook_url')
            lookup.current_title = result.get('current_title')
            lookup.current_company = result.get('current_company')
            lookup.location = result.get('location')
            lookup.confidence_score = result.get('confidence_score', 0)
            lookup.raw_response = result.get('raw_response', {})
            lookup.raw_data = result.get('raw_data', {})
            lookup.employee_emails = result.get('employee_emails', [])
            lookup.status = result.get('status', 'not_found')
            lookup.api_credits_used = 1
            
            # Store employee emails
            employee_emails = result.get('employee_emails', [])
            logger.info(f"Storing {len(employee_emails)} employee emails to database")
            
            logger.info(f"About to save lookup with {len(employee_emails)} employee emails")
            lookup.save()
            logger.info(f"Successfully saved lookup with {len(employee_emails)} employee emails")
            
            # Sync emails to Lawyer model based on entity type
            self._sync_emails_to_lawyer(lookup.lawyer, result)
        else:
            # Handle failed or no result case
            lookup.status = result.get('status', 'not_found') if result else 'failed'
            lookup.raw_response = result.get('raw_response', {}) if result else {}
            lookup.raw_data = result.get('raw_data', {}) if result else {}
            lookup.employee_emails = result.get('employee_emails', []) if result else []
            lookup.save()
    
    def _sync_emails_to_lawyer(self, lawyer, result) -> None:
        """Sync email data from RocketReach result to Lawyer model based on entity type"""
        try:
            employee_emails = result.get('employee_emails', [])
            best_email = result.get('email')
            
            if lawyer.entity_type == 'individual_attorney':
                # For Individual Attorney: Update primary email and company_emails
                self._sync_individual_attorney_emails(lawyer, best_email, employee_emails)
            elif lawyer.entity_type == 'law_firm':
                # For Law Firm: Update company_emails and employee_contacts
                self._sync_law_firm_emails(lawyer, best_email, employee_emails)
            else:
                # For unknown entity type, try to detect and sync
                self._sync_unknown_entity_emails(lawyer, best_email, employee_emails)
                
        except Exception as e:
            logger.error(f"Failed to sync emails to lawyer {lawyer.id}: {e}")
    
    def _sync_individual_attorney_emails(self, lawyer, best_email, employee_emails) -> None:
        """Sync emails for Individual Attorney entity type"""
        logger.info(f"Syncing emails for Individual Attorney: {lawyer.attorney_name}")
        
        # Update primary email if found
        if best_email and not lawyer.email:
            lawyer.email = best_email
            logger.info(f"Updated primary email for individual attorney: {best_email}")
        
        # Add all found emails to company_emails
        for emp in employee_emails:
            actual_emails = emp.get('actual_emails', [])
            for email_info in actual_emails:
                email = email_info.get('email')
                if email:
                    # Use Lawyer model's add_company_email method
                    lawyer.add_company_email(
                        email=email,
                        email_type=email_info.get('type', 'professional'),
                        contact_name=emp.get('name', 'N/A'),
                        contact_title=emp.get('title', 'Attorney'),
                        source='rocketreach',
                        confidence_score=0.8 if email_info.get('smtp_valid') == 'valid' else 0.5
                    )
                    logger.info(f"Added email for individual attorney: {email}")
        
        lawyer.save()
        logger.info(f"Completed syncing emails for Individual Attorney: {lawyer.attorney_name}")
    
    def _sync_law_firm_emails(self, lawyer, best_email, employee_emails) -> None:
        """Sync emails for Law Firm entity type"""
        logger.info(f"Syncing emails for Law Firm: {lawyer.company_name}")
        
        # For law firms, don't update primary email (should be empty or general contact)
        # Instead, add all emails to company_emails and employee_contacts
        
        for emp in employee_emails:
            actual_emails = emp.get('actual_emails', [])
            contact_name = emp.get('name', 'N/A')
            contact_title = emp.get('title', 'Attorney')
            
            # Add to company_emails
            for email_info in actual_emails:
                email = email_info.get('email')
                if email:
                    lawyer.add_company_email(
                        email=email,
                        email_type=email_info.get('type', 'professional'),
                        contact_name=contact_name,
                        contact_title=contact_title,
                        source='rocketreach',
                        confidence_score=0.8 if email_info.get('smtp_valid') == 'valid' else 0.5
                    )
                    logger.info(f"Added company email: {email} for {contact_name}")
            
            # Add to employee_contacts
            if actual_emails:
                employee_contact = {
                    'name': contact_name,
                    'title': contact_title,
                    'company': emp.get('company', lawyer.company_name),
                    'emails': [e.get('email') for e in actual_emails if e.get('email')],
                    'phone': emp.get('phone', ''),
                    'linkedin': emp.get('linkedin_url', ''),
                    'source': 'rocketreach',
                    'confidence': 'high' if actual_emails else 'low'
                }
                
                # Initialize employee_contacts if empty
                if not lawyer.employee_contacts:
                    lawyer.employee_contacts = []
                
                # Check if employee already exists
                existing_employee = None
                for existing in lawyer.employee_contacts:
                    if existing.get('name') == contact_name and existing.get('title') == contact_title:
                        existing_employee = existing
                        break
                
                if existing_employee:
                    # Update existing employee
                    existing_employee.update(employee_contact)
                else:
                    # Add new employee
                    lawyer.employee_contacts.append(employee_contact)
                
                logger.info(f"Added/updated employee contact: {contact_name}")
        
        lawyer.save()
        logger.info(f"Completed syncing emails for Law Firm: {lawyer.company_name}")
    
    def _sync_unknown_entity_emails(self, lawyer, best_email, employee_emails) -> None:
        """Sync emails for unknown entity type (try to detect and sync)"""
        logger.info(f"Syncing emails for unknown entity: {lawyer.company_name}")
        
        # Try to detect entity type based on employee_emails
        if len(employee_emails) == 1 and employee_emails[0].get('name') == lawyer.attorney_name:
            # Likely individual attorney
            self._sync_individual_attorney_emails(lawyer, best_email, employee_emails)
        else:
            # Likely law firm
            self._sync_law_firm_emails(lawyer, best_email, employee_emails)
    
    def get_lawyer_contact_list(self, lawyer_id: int = None, entity_type: str = None, 
                               limit: int = 50) -> Dict:
        """
        Get a visual list of lawyer contacts with name, email, company name
        
        Args:
            lawyer_id: Specific lawyer ID (optional)
            entity_type: Filter by entity type ('individual_attorney', 'law_firm', 'unknown')
            limit: Maximum number of results
            
        Returns:
            Dict containing contact list with summary statistics
        """
        from .models import Lawyer, RocketReachLookup
        
        try:
            # Build query
            lawyers_query = Lawyer.objects.filter(is_active=True)
            
            if lawyer_id:
                lawyers_query = lawyers_query.filter(id=lawyer_id)
            
            if entity_type:
                lawyers_query = lawyers_query.filter(entity_type=entity_type)
            
            lawyers = lawyers_query[:limit]
            
            contact_list = []
            stats = {
                'total_lawyers': 0,
                'individual_attorneys': 0,
                'law_firms': 0,
                'unknown_entities': 0,
                'lawyers_with_emails': 0,
                'total_emails_found': 0,
                'verified_emails': 0
            }
            
            for lawyer in lawyers:
                stats['total_lawyers'] += 1
                
                # Count by entity type
                if lawyer.entity_type == 'individual_attorney':
                    stats['individual_attorneys'] += 1
                elif lawyer.entity_type == 'law_firm':
                    stats['law_firms'] += 1
                else:
                    stats['unknown_entities'] += 1
                
                # Get all emails for this lawyer
                all_emails = lawyer.get_all_emails()
                verified_emails = lawyer.get_verified_emails()
                
                if all_emails:
                    stats['lawyers_with_emails'] += 1
                    stats['total_emails_found'] += len(all_emails)
                    stats['verified_emails'] += len(verified_emails)
                
                # Build contact entry
                contact_entry = {
                    'lawyer_id': lawyer.id,
                    'entity_type': lawyer.entity_type,
                    'company_name': lawyer.company_name,
                    'attorney_name': lawyer.attorney_name or 'N/A',
                    'primary_email': lawyer.email or 'N/A',
                    'phone': lawyer.phone or 'N/A',
                    'location': f"{lawyer.city}, {lawyer.state}" if lawyer.city and lawyer.state else lawyer.state or 'N/A',
                    'practice_area': lawyer.practice_area or 'N/A',
                    'website': lawyer.website or 'N/A',
                    'total_emails': len(all_emails),
                    'verified_emails': len(verified_emails),
                    'emails': all_emails,
                    'completeness_score': lawyer.completeness_score,
                    'quality_score': lawyer.quality_score,
                    'last_updated': lawyer.updated_at.isoformat() if lawyer.updated_at else 'N/A'
                }
                
                contact_list.append(contact_entry)
            
            return {
                'success': True,
                'contact_list': contact_list,
                'stats': stats,
                'query_params': {
                    'lawyer_id': lawyer_id,
                    'entity_type': entity_type,
                    'limit': limit
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get lawyer contact list: {e}")
            return {
                'success': False,
                'error': str(e),
                'contact_list': [],
                'stats': {}
            }
    
    def get_rocketreach_lookup_summary(self, lawyer_id: int = None, 
                                     status: str = None, limit: int = 50) -> Dict:
        """
        Get summary of RocketReach lookup results
        
        Args:
            lawyer_id: Specific lawyer ID (optional)
            status: Filter by lookup status ('completed', 'found', 'not_found', 'failed')
            limit: Maximum number of results
            
        Returns:
            Dict containing lookup summary
        """
        from .models import RocketReachLookup
        
        try:
            # Build query
            lookups_query = RocketReachLookup.objects.all()
            
            if lawyer_id:
                lookups_query = lookups_query.filter(lawyer_id=lawyer_id)
            
            if status:
                lookups_query = lookups_query.filter(status=status)
            
            lookups = lookups_query.order_by('-id')[:limit]
            
            lookup_summary = []
            stats = {
                'total_lookups': 0,
                'completed': 0,
                'found': 0,
                'not_found': 0,
                'failed': 0,
                'total_emails_found': 0,
                'total_employee_emails': 0
            }
            
            for lookup in lookups:
                stats['total_lookups'] += 1
                stats[lookup.status] = stats.get(lookup.status, 0) + 1
                
                # Count emails
                if lookup.email:
                    stats['total_emails_found'] += 1
                
                employee_emails = lookup.employee_emails or []
                stats['total_employee_emails'] += len(employee_emails)
                
                # Build lookup entry
                lookup_entry = {
                    'lookup_id': lookup.id,
                    'lawyer_id': lookup.lawyer.id,
                    'lawyer_name': lookup.lawyer.attorney_name or lookup.lawyer.company_name,
                    'company_name': lookup.lawyer.company_name,
                    'entity_type': lookup.lawyer.entity_type,
                    'status': lookup.status,
                    'email_found': lookup.email or 'N/A',
                    'phone_found': lookup.phone or 'N/A',
                    'linkedin_url': lookup.linkedin_url or 'N/A',
                    'current_title': lookup.current_title or 'N/A',
                    'current_company': lookup.current_company or 'N/A',
                    'location': lookup.location or 'N/A',
                    'confidence_score': lookup.confidence_score,
                    'employee_emails_count': len(employee_emails),
                    'employee_emails': employee_emails,
                    'api_credits_used': lookup.api_credits_used,
                    'created_at': lookup.lawyer.crawl_timestamp.isoformat() if lookup.lawyer.crawl_timestamp else 'N/A'
                }
                
                lookup_summary.append(lookup_entry)
            
            return {
                'success': True,
                'lookup_summary': lookup_summary,
                'stats': stats,
                'query_params': {
                    'lawyer_id': lawyer_id,
                    'status': status,
                    'limit': limit
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get RocketReach lookup summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'lookup_summary': [],
                'stats': {}
            }
    
    def export_contacts_to_csv_format(self, lawyer_id: int = None, 
                                    entity_type: str = None) -> str:
        """
        Export lawyer contacts to CSV format string
        
        Args:
            lawyer_id: Specific lawyer ID (optional)
            entity_type: Filter by entity type
            
        Returns:
            CSV formatted string
        """
        import csv
        import io
        
        try:
            result = self.get_lawyer_contact_list(lawyer_id, entity_type, limit=1000)
            
            if not result['success']:
                return f"Error: {result['error']}"
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Lawyer ID', 'Entity Type', 'Company Name', 'Attorney Name', 
                'Primary Email', 'Phone', 'Location', 'Practice Area', 
                'Website', 'Total Emails', 'Verified Emails', 
                'Completeness Score', 'Quality Score', 'Last Updated'
            ])
            
            # Write data rows
            for contact in result['contact_list']:
                writer.writerow([
                    contact['lawyer_id'],
                    contact['entity_type'],
                    contact['company_name'],
                    contact['attorney_name'],
                    contact['primary_email'],
                    contact['phone'],
                    contact['location'],
                    contact['practice_area'],
                    contact['website'],
                    contact['total_emails'],
                    contact['verified_emails'],
                    contact['completeness_score'],
                    contact['quality_score'],
                    contact['last_updated']
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to export contacts to CSV: {e}")
            return f"Error: {e}"

    def export_all_contacts_to_csv_file(self, file_path: str = 'lawyer_contacts_all.csv', 
                                       entity_type: Optional[str] = None, 
                                       batch_size: int = 500) -> str:
        """
        Export ALL lawyers to a CSV file efficiently in batches (suitable for 2k+ rows)
        
        Args:
            file_path: Destination CSV file path
            entity_type: Optional filter ("individual_attorney", "law_firm", "unknown")
            batch_size: Query batch size
        
        Returns:
            Absolute file path written
        """
        import csv
        import os
        from django.db.models import QuerySet
        from .models import Lawyer
        
        try:
            queryset: QuerySet = Lawyer.objects.filter(is_active=True)
            if entity_type:
                queryset = queryset.filter(entity_type=entity_type)
            
            # Order for deterministic export and memory-friendly iterator
            queryset = queryset.order_by('id')
            
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow([
                    'Lawyer ID', 'Entity Type', 'Company Name', 'Attorney Name',
                    'Primary Email', 'All Emails (first 3)', 'Phone', 'City', 'State',
                    'Practice Area', 'Website', 'Completeness', 'Quality', 'Updated At'
                ])
                
                count = 0
                for lawyer in queryset.iterator(chunk_size=batch_size):
                    all_emails = lawyer.get_all_emails()
                    primary_email = lawyer.email or (all_emails[0]['email'] if all_emails else '')
                    first_three_emails = ', '.join([e['email'] for e in all_emails[:3]]) if all_emails else ''
                    
                    writer.writerow([
                        lawyer.id,
                        lawyer.entity_type,
                        lawyer.company_name,
                        lawyer.attorney_name or '',
                        primary_email or '',
                        first_three_emails,
                        lawyer.phone or '',
                        lawyer.city or '',
                        lawyer.state or '',
                        lawyer.practice_area or '',
                        lawyer.website or '',
                        f"{lawyer.completeness_score}",
                        f"{lawyer.quality_score}",
                        lawyer.updated_at.isoformat() if lawyer.updated_at else ''
                    ])
                    count += 1
            
            abs_path = os.path.abspath(file_path)
            logger.info(f"Exported {count} lawyers to CSV: {abs_path}")
            return abs_path
        except Exception as e:
            logger.error(f"Failed to export all contacts to CSV: {e}")
            raise

    def export_emails_flat_csv_file(self, file_path: str = 'lawyer_emails_flat.csv',
                                    entity_type: Optional[str] = None,
                                    batch_size: int = 500) -> str:
        """
        Export a FLAT email-centric CSV: one row per email with key metadata.
        This makes emails prominent and easy to analyze.
        
        Columns:
        - Lawyer ID, Entity Type, Company Name, Attorney Name
        - Email, Email Type, Grade, Verified, Confidence, Source
        - Contact Name, Contact Title, Current Company
        - From Best (yes/no), Primary Email (yes/no)
        
        Returns absolute path of the written CSV file.
        """
        import csv
        import os
        from django.db.models import QuerySet
        from .models import Lawyer, RocketReachLookup
        
        try:
            queryset: QuerySet = Lawyer.objects.filter(is_active=True).order_by('id')
            if entity_type:
                queryset = queryset.filter(entity_type=entity_type)
            
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Lawyer ID', 'Entity Type', 'Company Name', 'Attorney Name',
                    'Email', 'Email Type', 'Grade', 'Verified', 'Confidence', 'Source',
                    'Contact Name', 'Contact Title', 'Current Company',
                    'From Best', 'Is Primary'
                ])
                
                for lawyer in queryset.iterator(chunk_size=batch_size):
                    all_emails = lawyer.get_all_emails() or []
                    primary_email_value = (lawyer.email or '').strip().lower()
                    best_email_value = primary_email_value
                    
                    # Try to infer best email from the latest lookup if primary is empty
                    if not best_email_value:
                        latest_lookup = RocketReachLookup.objects.filter(lawyer=lawyer).order_by('-id').first()
                        if latest_lookup and latest_lookup.email:
                            best_email_value = (latest_lookup.email or '').strip().lower()
                    
                    # Write rows for all known emails
                    for email_info in all_emails:
                        email_value = (email_info.get('email', '') or '').strip()
                        if not email_value:
                            continue
                        email_lower = email_value.lower()
                        
                        writer.writerow([
                            lawyer.id,
                            lawyer.entity_type,
                            lawyer.company_name,
                            lawyer.attorney_name or '',
                            email_value,
                            email_info.get('type', ''),
                            email_info.get('grade', ''),
                            email_info.get('verified', ''),
                            email_info.get('confidence', ''),
                            email_info.get('source', ''),
                            email_info.get('contact_name', ''),
                            email_info.get('contact_title', ''),
                            email_info.get('company', '') or lawyer.company_name,
                            'yes' if email_lower == best_email_value else 'no',
                            'yes' if email_lower == primary_email_value else 'no',
                        ])
                    
                    # If no emails captured at all, still write one row to track missing data
                    if not all_emails:
                        writer.writerow([
                            lawyer.id,
                            lawyer.entity_type,
                            lawyer.company_name,
                            lawyer.attorney_name or '',
                            '', '', '', '', '', '', '', '', '', 'no', 'no'
                        ])
            
            abs_path = os.path.abspath(file_path)
            logger.info(f"Exported flat emails CSV: {abs_path}")
            return abs_path
        except Exception as e:
            logger.error(f"Failed to export flat emails CSV: {e}")
            raise
    
    def _build_lookup_result(self, lawyer, result, lookup) -> Dict:
        """Build final lookup result"""
        if result and result.get('success') is not False:
            return {
                'success': True,
                'lawyer_id': lawyer.id,
                'lawyer_name': lawyer.attorney_name or lawyer.company_name,
                'email': result.get('email'),
                'confidence': result.get('confidence_score', 0),
                'status': lookup.status,
                'lookup_id': lookup.id
            }
        else:
            return {
                'success': result.get('success', False) if result else False,
                'lawyer_id': lawyer.id,
                'lawyer_name': lawyer.attorney_name or lawyer.company_name,
                'email': result.get('email') if result else None,
                'confidence': result.get('confidence_score', 0) if result else 0,
                'status': lookup.status,
                'lookup_id': lookup.id,
                'error': result.get('error') if result else 'No result returned'
            }
