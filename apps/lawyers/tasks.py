from celery import shared_task
from django.utils import timezone
from .models import Lawyer


@shared_task
def crawl_single_url(task_id):
    """Crawl a single URL and save lawyers"""
    # This will be implemented in the crawler app
    pass


@shared_task
def calculate_quality_scores():
    """Calculate quality scores for all lawyers"""
    lawyers = Lawyer.objects.all()
    
    for lawyer in lawyers:
        # Calculate completeness score
        fields = [
            lawyer.company_name, lawyer.phone, lawyer.address,
            lawyer.practice_areas, lawyer.website, lawyer.email
        ]
        filled_fields = sum(1 for field in fields if field)
        completeness_score = (filled_fields / len(fields)) * 100
        
        # Calculate quality score (based on data quality)
        quality_score = 0
        
        # Phone format validation
        if lawyer.phone and len(lawyer.phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 10:
            quality_score += 20
        
        # Email validation
        if lawyer.email and '@' in lawyer.email and '.' in lawyer.email:
            quality_score += 20
        
        # Website validation
        if lawyer.website and (lawyer.website.startswith('http') or lawyer.website.startswith('www')):
            quality_score += 20
        
        # Address completeness
        if lawyer.address and len(lawyer.address) > 20:
            quality_score += 20
        
        # Company name quality
        if lawyer.company_name and len(lawyer.company_name) > 5:
            quality_score += 20
        
        # Update lawyer
        lawyer.completeness_score = completeness_score
        lawyer.quality_score = quality_score
        lawyer.save()
    
    return f"Updated quality scores for {lawyers.count()} lawyers"


@shared_task
def cleanup_duplicate_lawyers():
    """Remove duplicate lawyers based on company name and location"""
    from django.db.models import Count
    
    # Find duplicates
    duplicates = Lawyer.objects.values('company_name', 'city', 'state').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    removed_count = 0
    
    for duplicate in duplicates:
        lawyers = Lawyer.objects.filter(
            company_name=duplicate['company_name'],
            city=duplicate['city'],
            state=duplicate['state']
        ).order_by('-crawl_timestamp')
        
        # Keep the most recent one, remove others
        to_remove = lawyers[1:]
        for lawyer in to_remove:
            lawyer.delete()
            removed_count += 1
    
    return f"Removed {removed_count} duplicate lawyers"


@shared_task
def export_lawyers_data(format_type='csv'):
    """Export lawyers data to file"""
    import csv
    import json
    from django.conf import settings
    import os
    
    lawyers = Lawyer.objects.filter(is_active=True)
    
    if format_type == 'csv':
        filename = f"lawyers_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Company Name', 'Phone', 'Email', 'Address', 'Website',
                'Domain', 'State', 'City', 'Practice Area', 'Crawl Date'
            ])
            
            for lawyer in lawyers:
                writer.writerow([
                    lawyer.company_name,
                    lawyer.phone,
                    lawyer.email,
                    lawyer.address,
                    lawyer.website,
                    lawyer.domain,
                    lawyer.state,
                    lawyer.city,
                    lawyer.practice_area,
                    lawyer.crawl_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        return f"Exported {lawyers.count()} lawyers to {filename}"
    
    elif format_type == 'json':
        filename = f"lawyers_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(settings.MEDIA_ROOT, 'exports', filename)
        
        # Create directory if not exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = []
        for lawyer in lawyers:
            data.append({
                'company_name': lawyer.company_name,
                'phone': lawyer.phone,
                'email': lawyer.email,
                'address': lawyer.address,
                'website': lawyer.website,
                'domain': lawyer.domain,
                'state': lawyer.state,
                'city': lawyer.city,
                'practice_area': lawyer.practice_area,
                'crawl_timestamp': lawyer.crawl_timestamp.isoformat()
            })
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        return f"Exported {lawyers.count()} lawyers to {filename}"
    
    return "Invalid format type"
