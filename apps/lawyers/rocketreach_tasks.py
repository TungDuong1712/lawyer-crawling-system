"""
Celery tasks for RocketReach email lookup
"""

from celery import shared_task
from django.conf import settings
import logging
import os
from typing import List, Dict

from .models import Lawyer, RocketReachLookup
from .rocketreach_api_service import RocketReachLookupService
from .rocketreach_web_crawler import run_rocketreach_keyword_search

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def lookup_lawyer_email_task(self, lawyer_id: int, force_refresh: bool = False):
    """
    Celery task to lookup email for a single lawyer
    
    Args:
        lawyer_id: ID of the Lawyer instance
        force_refresh: Force new lookup even if previous exists
        
    Returns:
        Dict with lookup results
    """
    try:
        # Get lawyer instance
        lawyer = Lawyer.objects.get(id=lawyer_id)
        
        # Initialize RocketReach service
        api_key = getattr(settings, 'ROCKETREACH_API_KEY', None) or os.getenv('ROCKETREACH_API_KEY')
        print(f"DEBUG: ROCKETREACH_API_KEY from settings: {api_key}")
        if not api_key:
            raise ValueError("ROCKETREACH_API_KEY not configured")
        
        service = RocketReachLookupService(api_key)
        
        # Perform lookup
        lookup = service.lookup_lawyer_email(lawyer_id, force_refresh)
        
        # lookup is now a dict, not an object
        if lookup and lookup.get('success'):
            return {
                'success': True,
                'lawyer_id': lawyer_id,
                'lawyer_name': lawyer.company_name,
                'email': lookup.get('email'),
                'confidence': lookup.get('confidence', 0),
                'status': lookup.get('status'),
                'lookup_id': lookup.get('lookup_id')
            }
        else:
            return {
                'success': False,
                'lawyer_id': lawyer_id,
                'lawyer_name': lawyer.company_name,
                'error': lookup.get('error', 'Lookup failed') if lookup else 'Lookup failed'
            }
            
    except Lawyer.DoesNotExist:
        logger.error(f"Lawyer with ID {lawyer_id} not found")
        return {
            'success': False,
            'lawyer_id': lawyer_id,
            'error': 'Lawyer not found'
        }
    except Exception as e:
        logger.error(f"Failed to lookup email for lawyer {lawyer_id}: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'lawyer_id': lawyer_id,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=2)
def web_lookup_keyword_task(self, keyword: str, headless: bool = True):
    """Perform RocketReach web automation lookup by keyword using Playwright."""
    try:
        result = run_rocketreach_keyword_search(keyword=keyword, headless=headless)
        return result
    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def bulk_lookup_lawyers_task(self, lawyer_ids: List[int], batch_size: int = 10):
    """
    Celery task to lookup emails for multiple lawyers
    
    Args:
        lawyer_ids: List of Lawyer IDs
        batch_size: Number of lawyers to process in each batch
        
    Returns:
        Dict with bulk lookup results
    """
    try:
        # Get lawyers
        lawyers = Lawyer.objects.filter(id__in=lawyer_ids)
        
        if not lawyers.exists():
            return {
                'success': False,
                'error': 'No lawyers found with provided IDs'
            }
        
        # Initialize RocketReach service
        api_key = getattr(settings, 'ROCKETREACH_API_KEY', None)
        if not api_key:
            raise ValueError("ROCKETREACH_API_KEY not configured")
        
        service = RocketReachLookupService(api_key)
        
        # Perform bulk lookup
        results = service.bulk_lookup_lawyers(lawyers, batch_size)
        
        # Calculate statistics
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        return {
            'success': True,
            'total_lawyers': total,
            'successful_lookups': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Failed to bulk lookup lawyers: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def lookup_lawyers_without_email_task(self, domain: str = None, limit: int = 100):
    """
    Celery task to lookup emails for lawyers who don't have email addresses
    
    Args:
        domain: Filter by domain (optional)
        limit: Maximum number of lawyers to process
        
    Returns:
        Dict with lookup results
    """
    try:
        # Get lawyers without email
        lawyers_query = Lawyer.objects.filter(email__isnull=True).exclude(email='')
        
        if domain:
            lawyers_query = lawyers_query.filter(domain=domain)
        
        lawyers = lawyers_query[:limit]
        
        if not lawyers.exists():
            return {
                'success': True,
                'message': 'No lawyers found without email addresses',
                'total_processed': 0
            }
        
        # Initialize RocketReach service
        api_key = getattr(settings, 'ROCKETREACH_API_KEY', None)
        if not api_key:
            raise ValueError("ROCKETREACH_API_KEY not configured")
        
        service = RocketReachLookupService(api_key)
        
        # Process lawyers
        results = []
        for lawyer in lawyers:
            try:
                lookup = service.lookup_lawyer_email(lawyer)
                results.append({
                    'lawyer_id': lawyer.id,
                    'lawyer_name': lawyer.company_name,
                    'success': lookup is not None and lookup.is_successful(),
                    'email': lookup.email if lookup else None,
                    'confidence': lookup.confidence_score if lookup else 0
                })
            except Exception as e:
                logger.error(f"Failed to lookup {lawyer.company_name}: {e}")
                results.append({
                    'lawyer_id': lawyer.id,
                    'lawyer_name': lawyer.company_name,
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate statistics
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        return {
            'success': True,
            'total_processed': total,
            'successful_lookups': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Failed to lookup lawyers without email: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def update_lawyer_emails_from_rocketreach_task(self):
    """
    Celery task to update lawyer emails from successful RocketReach lookups
    
    Returns:
        Dict with update results
    """
    try:
        # Get successful lookups that haven't been applied to lawyers
        successful_lookups = RocketReachLookup.objects.filter(
            status='completed',
            email__isnull=False
        ).exclude(email='')
        
        updated_count = 0
        results = []
        
        for lookup in successful_lookups:
            try:
                # Update lawyer email if not already set
                if not lookup.lawyer.email:
                    lookup.lawyer.email = lookup.email
                    lookup.lawyer.save(update_fields=['email'])
                    updated_count += 1
                    
                    results.append({
                        'lawyer_id': lookup.lawyer.id,
                        'lawyer_name': lookup.lawyer.company_name,
                        'email': lookup.email,
                        'confidence': lookup.confidence_score
                    })
                    
            except Exception as e:
                logger.error(f"Failed to update email for {lookup.lawyer.company_name}: {e}")
                results.append({
                    'lawyer_id': lookup.lawyer.id,
                    'lawyer_name': lookup.lawyer.company_name,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'total_updated': updated_count,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Failed to update lawyer emails: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def cleanup_failed_lookups_task(self, days_old: int = 7):
    """
    Celery task to cleanup old failed lookups
    
    Args:
        days_old: Number of days old to consider for cleanup
        
    Returns:
        Dict with cleanup results
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Get old failed lookups
        old_failed_lookups = RocketReachLookup.objects.filter(
            status__in=['failed', 'not_found'],
            lookup_timestamp__lt=cutoff_date
        )
        
        count = old_failed_lookups.count()
        old_failed_lookups.delete()
        
        return {
            'success': True,
            'deleted_count': count,
            'message': f'Deleted {count} old failed lookups'
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup failed lookups: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def crawl_rocketreach_web_task(self, base_url: str, max_pages: int = 10, headless: bool = True):
    """
    Celery task to crawl RocketReach web interface with pagination
    
    Args:
        base_url: RocketReach search URL
        max_pages: Maximum number of pages to crawl
        headless: Run browser in headless mode
        
    Returns:
        Dict with crawling results
    """
    try:
        logger.info(f"Starting RocketReach web crawl task for: {base_url}")
        
        # Run the web crawler
        result = run_rocketreach_web_crawl(
            base_url=base_url,
            headless=headless,
            max_pages=max_pages
        )
        
        if result['success']:
            logger.info(
                f"Web crawling completed: {result['total_contacts']} contacts found, "
                f"{result['saved_contacts']} saved to DB"
            )
        else:
            logger.error(f"Web crawling failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"RocketReach web crawl task failed: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"Task failed after {self.max_retries} retries")
            return {
                'success': False,
                'error': f'Task failed after {self.max_retries} retries: {str(e)}',
                'contacts': []
            }


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def search_rocketreach_keyword_task(self, keyword: str, headless: bool = True):
    """
    Celery task to search RocketReach by keyword and get contact info
    
    Args:
        keyword: Search keyword
        headless: Run browser in headless mode
        
    Returns:
        Dict with search results
    """
    try:
        logger.info(f"Starting RocketReach keyword search task for: {keyword}")
        
        # Run the keyword search
        result = run_rocketreach_keyword_search(
            keyword=keyword,
            headless=headless
        )
        
        if result['success']:
            emails = result.get('emails', [])
            logger.info(f"Keyword search completed: {len(emails)} emails found for '{keyword}'")
        else:
            logger.error(f"Keyword search failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"RocketReach keyword search task failed: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"Task failed after {self.max_retries} retries")
            return {
                'success': False,
                'error': f'Task failed after {self.max_retries} retries: {str(e)}',
                'emails': []
            }


@shared_task
def crawl_law_industry_contacts(max_pages: int = 20, headless: bool = True):
    """
    Convenience task to crawl law industry contacts from RocketReach
    
    Args:
        max_pages: Maximum number of pages to crawl
        headless: Run browser in headless mode
        
    Returns:
        Dict with crawling results
    """
    base_url = "https://rocketreach.co/person?company_industry%5B%5D=Law+Firms+%26+Legal+Services&start=1&pageSize=20"
    
    return crawl_rocketreach_web_task.delay(
        base_url=base_url,
        max_pages=max_pages,
        headless=headless
    )


@shared_task
def crawl_contacts_by_keyword(keyword: str, max_pages: int = 10, headless: bool = True):
    """
    Crawl contacts by keyword search
    
    Args:
        keyword: Search keyword
        max_pages: Maximum number of pages to crawl
        headless: Run browser in headless mode
        
    Returns:
        Dict with crawling results
    """
    from urllib.parse import quote
    
    base_url = f"https://rocketreach.co/person?keyword={quote(keyword)}&start=1&pageSize=20"
    
    return crawl_rocketreach_web_task.delay(
        base_url=base_url,
        max_pages=max_pages,
        headless=headless
    )


@shared_task
def bulk_crawl_rocketreach_urls(urls: List[str], max_pages: int = 5, headless: bool = True):
    """
    Bulk crawl multiple RocketReach URLs
    
    Args:
        urls: List of RocketReach search URLs
        max_pages: Maximum number of pages per URL
        headless: Run browser in headless mode
        
    Returns:
        Dict with bulk crawling results
    """
    try:
        results = []
        total_contacts = 0
        total_saved = 0
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
                
                result = run_rocketreach_web_crawl(
                    base_url=url,
                    headless=headless,
                    max_pages=max_pages
                )
                
                results.append({
                    'url': url,
                    'success': result['success'],
                    'contacts_found': result.get('total_contacts', 0),
                    'contacts_saved': result.get('saved_contacts', 0),
                    'error': result.get('error') if not result['success'] else None
                })
                
                if result['success']:
                    total_contacts += result.get('total_contacts', 0)
                    total_saved += result.get('saved_contacts', 0)
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                results.append({
                    'url': url,
                    'success': False,
                    'contacts_found': 0,
                    'contacts_saved': 0,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'total_urls': len(urls),
            'total_contacts_found': total_contacts,
            'total_contacts_saved': total_saved,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Bulk crawl failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': []
        }
