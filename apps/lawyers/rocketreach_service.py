import requests
import time
import logging
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class RocketReachAPI:
    """RocketReach API client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.BASE_URL = "https://api.rocketreach.co/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        })
    
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
        # Use correct payload format for RocketReach API based on documentation
        payload = {
            "query": {
                "name": [name] if name else [],
                "current_employer": [company] if company else [],
                "current_title": [title] if title else [],
                "location": [location] if location else []
            },
            "page_size": 10,
            "start": 1
        }
        
        try:
            # Use the People Search API endpoint
            # Add delay to avoid rate limiting
            time.sleep(30)  # Very slow delay to avoid rate limiting
            response = self.session.post(f"{self.BASE_URL}/person/search", json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                logger.warning(f"Rate limit exceeded, waiting 60 seconds before retry...")
                time.sleep(60)
                # Retry once
                response = self.session.post(f"{self.BASE_URL}/person/search", json=payload)
                response.raise_for_status()
                return response.json()
            else:
                logger.error(f"HTTP error in search person: {e}")
                raise
        except requests.RequestException as e:
            logger.error(f"Failed to search person: {e}")
            raise


class RocketReachLookupService:
    """Service for looking up lawyer emails using RocketReach API"""
    
    def __init__(self, api_key: str):
        self.api = RocketReachAPI(api_key)
    
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
            
            # Store raw API responses for debugging
            raw_responses = {}
            
            # Use person/search API
            search_results = self.api.search_person(
                name=lawyer_name,
                company=company_name,
                location=location
            )
            raw_responses['person_search'] = search_results
            logger.info(f"Person search results: {search_results}")
            
            # Process results - RocketReach API returns 'profiles' field
            profiles = search_results.get('profiles', [])
            if not profiles:
                # Fallback to 'people' if 'profiles' is empty (new format)
                profiles = search_results.get('people', [])
            logger.info(f"Found {len(profiles)} profiles")
            
            # Initialize variables
            best_match = None
            employee_emails = []
            
            if profiles:
                # Get the best match
                best_match = profiles[0]
                logger.info(f"Best match: {best_match}")
                
                # Process all profiles
                for i, profile in enumerate(profiles):
                    name = profile.get('name', 'N/A')
                    title = profile.get('current_title', 'N/A')
                    company = profile.get('current_employer', 'N/A')
                    current_employer_domain = profile.get('current_employer_domain', '')
                    
                    logger.info(f"Profile {i+1}: {name} - {title} at {company} (domain: {current_employer_domain})")
                    
                    # Generate email patterns from domain
                    full_emails = []
                    if current_employer_domain:
                        name_parts = name.lower().split()
                        if len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = name_parts[-1]
                            
                            # Common email patterns
                            patterns = [
                                f"{first_name}.{last_name}@{current_employer_domain}",
                                f"{first_name}{last_name}@{current_employer_domain}",
                                f"{first_name[0]}{last_name}@{current_employer_domain}",
                            ]
                            full_emails = patterns
                            logger.info(f"Generated email patterns for {name}: {full_emails}")
                    
                    # Store profile as employee email
                    employee_emails.append({
                        'name': name,
                        'title': title,
                        'company': company,
                        'email_domain': current_employer_domain,
                        'email_type': 'current_company',
                        'source': 'current_employer_domain',
                        'confidence': 'medium',
                        'full_emails': full_emails,
                        'match_score': 0.5
                    })
            
            # Extract information from API response
            raw_response_data = search_results
            
            # Use best match if found
            if best_match:
                # Extract the best email from full_emails
                best_email = None
                if employee_emails and employee_emails[0].get('full_emails'):
                    best_email = employee_emails[0]['full_emails'][0]  # Use first pattern
                
                result = {
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
            else:
                # No profiles found
                result = {
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
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to find email for {company_name or lawyer_name}: {e}")
            return None
    
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
                existing_lookup = RocketReachLookup.objects.filter(
                    lawyer=lawyer,
                    status__in=['completed', 'found']
                ).first()
                
                if existing_lookup:
                    logger.info(f"Lawyer {lawyer_id} already looked up, returning existing result")
                    return {
                        'success': True,
                        'lawyer_id': lawyer_id,
                        'lawyer_name': lawyer.attorney_name or lawyer.company_name,
                        'email': existing_lookup.email,
                        'confidence': existing_lookup.confidence_score,
                        'status': existing_lookup.status,
                        'lookup_id': existing_lookup.id
                    }
            
            # Create new lookup record
            lookup = RocketReachLookup.objects.create(
                lawyer=lawyer,
                status='in_progress'
            )
            
            # Find email using RocketReach
            result = self.find_lawyer_email(
                lawyer_name=lawyer.attorney_name,
                company_name=lawyer.company_name,
                domain=lawyer.domain,
                location=lawyer.state
            )
            
            if result:
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
                lookup.status = 'found' if result.get('email') else 'not_found'
                lookup.api_credits_used = 1
                
                # Store employee emails
                employee_emails = result.get('employee_emails', [])
                logger.info(f"Storing {len(employee_emails)} employee emails to database")
                
                lookup.employee_emails = employee_emails
                
                logger.info(f"About to save lookup with {len(employee_emails)} employee emails")
                lookup.save()
                logger.info(f"Successfully saved lookup with {len(employee_emails)} employee emails")
                
                return {
                    'success': True,
                    'lawyer_id': lawyer_id,
                    'lawyer_name': lawyer.attorney_name or lawyer.company_name,
                    'email': result.get('email'),
                    'confidence': result.get('confidence_score', 0),
                    'status': lookup.status,
                    'lookup_id': lookup.id
                }
            else:
                lookup.status = 'not_found'
                lookup.save()
                
                return {
                    'success': True,
                    'lawyer_id': lawyer_id,
                    'lawyer_name': lawyer.attorney_name or lawyer.company_name,
                    'email': None,
                    'confidence': 0,
                    'status': 'not_found',
                    'lookup_id': lookup.id
                }
                
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
