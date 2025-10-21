from celery import shared_task
from django.utils import timezone
from .models import CrawlSession, CrawlTask
from apps.lawyers.models import Lawyer
from apps.lawyers.tasks import crawl_single_url
import json


@shared_task
def start_crawl_session(session_id):
    """Start a crawl session"""
    try:
        session = CrawlSession.objects.get(id=session_id)
        
        # Generate URLs based on session parameters
        from url_generator import URLGenerator
        generator = URLGenerator()
        
        urls = []
        if session.domains and session.states and session.practice_areas:
            # Custom parameters
            for domain in session.domains:
                for state in session.states:
                    for practice_area in session.practice_areas:
                        domain_urls = generator.generate_urls_for_domain(domain)
                        filtered_urls = [url for url in domain_urls 
                                        if url['state'] == state and url['practice_area'] == practice_area]
                        urls.extend(filtered_urls[:session.limit])
        else:
            # Default: all combinations
            urls = generator.generate_urls()[:session.limit]
        
        session.total_urls = len(urls)
        session.save()
        
        # Create crawl tasks
        for url_info in urls:
            task = CrawlTask.objects.create(
                session=session,
                url=url_info['url'],
                domain=url_info['domain'],
                state=url_info['state'],
                city=url_info['city'],
                practice_area=url_info['practice_area']
            )
            
            # Start individual crawl task
            crawl_single_url.delay(task.id)
        
        return f"Started crawl session {session_id} with {len(urls)} URLs"
        
    except CrawlSession.DoesNotExist:
        return f"Session {session_id} not found"
    except Exception as e:
        return f"Error starting session {session_id}: {str(e)}"


@shared_task
def crawl_single_url(task_id):
    """Crawl a single URL"""
    try:
        task = CrawlTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.save()
        
        # Import crawler here to avoid circular imports
        from lawyer_crawler import LawyerCrawler
        
        crawler = LawyerCrawler()
        url_info = {
            'url': task.url,
            'domain': task.domain,
            'state': task.state,
            'city': task.city,
            'practice_area': task.practice_area,
            'selectors': {}  # Will be loaded from config
        }
        
        # Crawl the URL
        lawyers_data = crawler.crawl_lawyer_info(url_info)
        
        # Save lawyers to database
        lawyers_saved = 0
        for lawyer_data in lawyers_data:
            lawyer, created = Lawyer.objects.get_or_create(
                source_url=lawyer_data['source_url'],
                company_name=lawyer_data.get('company_name', ''),
                defaults={
                    'domain': lawyer_data.get('domain', ''),
                    'practice_area': lawyer_data.get('practice_area', ''),
                    'state': lawyer_data.get('state', ''),
                    'city': lawyer_data.get('city', ''),
                    'phone': lawyer_data.get('phone', ''),
                    'address': lawyer_data.get('address', ''),
                    'practice_areas': lawyer_data.get('practice_areas', ''),
                    'attorney_details': lawyer_data.get('attorney_details', ''),
                    'website': lawyer_data.get('website', ''),
                    'email': lawyer_data.get('email', ''),
                }
            )
            if created:
                lawyers_saved += 1
        
        # Update task
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.lawyers_found = lawyers_saved
        task.save()
        
        # Update session
        session = task.session
        session.crawled_urls += 1
        session.success_count += lawyers_saved
        session.save()
        
        return f"Task {task_id} completed: {lawyers_saved} lawyers found"
        
    except CrawlTask.DoesNotExist:
        return f"Task {task_id} not found"
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save()
        
        # Update session
        session = task.session
        session.crawled_urls += 1
        session.error_count += 1
        session.save()
        
        return f"Task {task_id} failed: {str(e)}"
