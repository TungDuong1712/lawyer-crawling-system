from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import SourceConfiguration, DiscoveryURL
from .tasks import crawl_session_task, update_crawl_progress
from apps.lawyers.models import Lawyer


@admin.register(SourceConfiguration)
class SourceConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'progress_percentage', 'created_by', 'created_at', 'total_urls', 'crawled_urls', 'success_count']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'last_updated', 'progress_percentage']
    actions = ['start_crawl_workflow', 'reset_crawl_status', 'download_lawyers_data']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status', 'created_by')
        }),
        ('Start URLs', {
            'fields': ('start_urls',),
            'description': 'List of URLs to crawl, e.g., ["www.lawinfo.com/personal-injury/arizona/chandler/"]'
        }),
        ('Selectors', {
            'fields': ('selectors',),
            'description': 'JSON field storing XPath selectors for data extraction'
        }),
        ('Configuration', {
            'fields': ('delay_between_requests', 'max_retries', 'timeout')
        }),
        ('Progress', {
            'fields': ('total_urls', 'crawled_urls', 'success_count', 'error_count', 'progress_percentage'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def progress_percentage(self, obj):
        """Display progress as a colored bar"""
        if obj.progress_percentage == 0:
            color = 'red'
        elif obj.progress_percentage < 50:
            color = 'orange'
        elif obj.progress_percentage < 100:
            color = 'blue'
        else:
            color = 'green'
        
        return format_html(
            '<div style="width: 100px; background-color: {}; color: white; text-align: center; padding: 2px;">{:.1f}%</div>',
            color, obj.progress_percentage
        )
    progress_percentage.short_description = 'Progress'
    
    def start_crawl_workflow(self, request, queryset):
        """Start crawl workflow for start URLs"""
        for source in queryset:
            if source.status == 'PENDING':
                source.status = 'CRAWLING'
                source.save()
                # TODO: Start crawling tasks for start_urls
                self.message_user(request, f"Started crawl workflow for {source.name}")
    start_crawl_workflow.short_description = "Start Crawl Workflow"
    
    def reset_crawl_status(self, request, queryset):
        """Reset crawl status"""
        for source in queryset:
            source.status = 'PENDING'
            source.progress_percentage = 0.0
            source.save()
            self.message_user(request, f"Reset status for {source.name}")
    reset_crawl_status.short_description = "Reset Status"


@admin.register(DiscoveryURL)
class DiscoveryURLAdmin(admin.ModelAdmin):
    list_display = ['source_config', 'domain', 'practice_area', 'city', 'status', 'lawyers_found', 'created_at']
    list_filter = ['status', 'domain', 'practice_area', 'state', 'created_at']
    search_fields = ['url', 'domain', 'city', 'source_config__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    actions = ['retry_failed_urls', 'mark_as_pending']
    
    def retry_failed_urls(self, request, queryset):
        """Retry failed URLs"""
        from .tasks import crawl_lawyer_info_task
        for url in queryset.filter(status='FAILED'):
            url.status = 'PENDING'
            url.error_message = ''
            url.save()
            crawl_lawyer_info_task.delay(url.id)
        self.message_user(request, f"Retrying {queryset.filter(status='FAILED').count()} failed URLs")
    retry_failed_urls.short_description = "Retry Failed URLs"
    
    def mark_as_pending(self, request, queryset):
        """Mark URLs as pending"""
        queryset.update(status='PENDING', error_message='')
        self.message_user(request, f"Marked {queryset.count()} URLs as pending")
    mark_as_pending.short_description = "Mark as Pending"




# LawyerAdmin is already registered in apps.lawyers.admin


# Add download_lawyers_data action
def download_lawyers_data(self, request, queryset):
    """Download lawyers data as CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lawyers_data.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Phone', 'Email', 'Address', 'Company', 'Practice Area', 'City', 'State'])
    
    for source in queryset:
        lawyers = Lawyer.objects.filter(source_url__in=source.start_urls)
        for lawyer in lawyers:
            writer.writerow([
                lawyer.name,
                lawyer.phone,
                lawyer.email,
                lawyer.address,
                lawyer.company_name,
                lawyer.practice_area,
                lawyer.city,
                lawyer.state
            ])
    
    return response
download_lawyers_data.short_description = "Download Lawyers Data"

# Add method to SourceConfigurationAdmin
SourceConfigurationAdmin.download_lawyers_data = download_lawyers_data
