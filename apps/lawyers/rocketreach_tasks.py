"""
Celery tasks for RocketReach email lookup
"""

from celery import shared_task
from django.conf import settings
import logging
from typing import List, Dict

from .models import Lawyer, RocketReachLookup
from .rocketreach_service import RocketReachLookupService

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
        api_key = getattr(settings, 'ROCKETREACH_API_KEY', None)
        if not api_key:
            raise ValueError("ROCKETREACH_API_KEY not configured")
        
        service = RocketReachLookupService(api_key)
        
        # Perform lookup
        lookup = service.lookup_lawyer_email(lawyer, force_refresh)
        
        if lookup:
            return {
                'success': True,
                'lawyer_id': lawyer_id,
                'lawyer_name': lawyer.company_name,
                'email': lookup.email,
                'confidence': lookup.confidence_score,
                'status': lookup.status,
                'lookup_id': lookup.id
            }
        else:
            return {
                'success': False,
                'lawyer_id': lawyer_id,
                'lawyer_name': lawyer.company_name,
                'error': 'Lookup failed'
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
