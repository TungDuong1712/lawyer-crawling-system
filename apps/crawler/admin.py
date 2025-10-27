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
    actions = ['step1_crawl_basic', 'step2_crawl_detail', 'full_flow_crawl', 'rocketreach_lookups', 'clear_celery_tasks', 'download_lawyers_data']
    
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
    
    def step1_crawl_basic(self, request, queryset):
        """Step 1: Crawl basic lawyer info only"""
        from apps.crawler.tasks import crawl_session_task
        
        started_count = 0
        for source in queryset:
            if source.status != 'CRAWLING':
                source.status = 'CRAWLING'
                source.save()
                
                try:
                    task = crawl_session_task.delay(source.id)
                    started_count += 1
                    self.message_user(request, f"Started Step 1 (basic crawl) for {source.name} (Task ID: {task.id})")
                except Exception as e:
                    source.status = 'PENDING'
                    source.save()
                    self.message_user(request, f"Failed to start Step 1 for {source.name}: {e}", level='ERROR')
        
        if started_count > 0:
            self.message_user(request, f"Started {started_count} Step 1 crawl workflows")
        else:
            self.message_user(request, "No sources available to start Step 1", level='WARNING')
    step1_crawl_basic.short_description = "Step 1: Crawl Basic Info"
    
    
    def step2_crawl_detail(self, request, queryset):
        """Step 2: Crawl detailed info only"""
        from apps.crawler.tasks import crawl_lawyer_detail_task
        from apps.lawyers.models import Lawyer
        
        total_queued = 0
        for source in queryset:
            # Get lawyers from this source that need detail crawling
            lawyers = Lawyer.objects.filter(
                source_url__in=source.start_urls,
                is_detail_crawled=False,
                detail_url__isnull=False
            ).exclude(detail_url='')
            
            if lawyers.exists():
                # Queue detail crawl tasks
                for lawyer in lawyers:
                    try:
                        crawl_lawyer_detail_task.delay(lawyer.id)
                        total_queued += 1
                    except Exception as e:
                        self.message_user(request, f"Failed to queue detail crawl for {lawyer.company_name}: {e}", level='ERROR')
                
                self.message_user(request, f"Queued {lawyers.count()} detail crawl tasks for {source.name}")
            else:
                self.message_user(request, f"No lawyers need detail crawling for {source.name}", level='WARNING')
        
        if total_queued > 0:
            self.message_user(request, f"Queued {total_queued} detail crawl tasks")
        else:
            self.message_user(request, "No lawyers available for detail crawling", level='WARNING')
    step2_crawl_detail.short_description = "Step 2: Crawl Detail Info"
    
    def full_flow_crawl(self, request, queryset):
        """Full Flow: Step 1 + Step 2"""
        from apps.crawler.tasks import crawl_session_task, crawl_lawyer_detail_task
        from apps.lawyers.models import Lawyer
        
        started_count = 0
        for source in queryset:
            if source.status != 'CRAWLING':
                source.status = 'CRAWLING'
                source.save()
                
                try:
                    # Start Step 1
                    task = crawl_session_task.delay(source.id)
                    started_count += 1
                    self.message_user(request, f"Started Full Flow (Step 1 + Step 2) for {source.name} (Task ID: {task.id})")
                    
                    # Note: Step 2 will be triggered automatically after Step 1 completes
                    # or can be triggered manually later
                    
                except Exception as e:
                    source.status = 'PENDING'
                    source.save()
                    self.message_user(request, f"Failed to start Full Flow for {source.name}: {e}", level='ERROR')
        
        if started_count > 0:
            self.message_user(request, f"Started {started_count} Full Flow crawl workflows")
        else:
            self.message_user(request, "No sources available to start Full Flow", level='WARNING')
    full_flow_crawl.short_description = "Full Flow: Step 1 + Step 2"
    
    def rocketreach_lookups(self, request, queryset):
        """RocketReach Lookups: Find emails for lawyers"""
        from apps.lawyers.rocketreach_tasks import lookup_lawyer_email_task
        from apps.lawyers.models import Lawyer
        
        total_queued = 0
        for source in queryset:
            # Get lawyers from this source that need email lookup
            lawyers = Lawyer.objects.filter(
                source_url__in=source.start_urls,
                email__isnull=True
            ).exclude(email='')
            
            if lawyers.exists():
                # Queue RocketReach lookup tasks
                for lawyer in lawyers:
                    try:
                        lookup_lawyer_email_task.delay(lawyer.id)
                        total_queued += 1
                    except Exception as e:
                        self.message_user(request, f"Failed to queue RocketReach lookup for {lawyer.company_name}: {e}", level='ERROR')
                
                self.message_user(request, f"Queued {lawyers.count()} RocketReach lookups for {source.name}")
            else:
                self.message_user(request, f"No lawyers need email lookup for {source.name}", level='WARNING')
        
        if total_queued > 0:
            self.message_user(request, f"Queued {total_queued} RocketReach lookup tasks")
        else:
            self.message_user(request, "No lawyers available for RocketReach lookup", level='WARNING')
    rocketreach_lookups.short_description = "RocketReach Lookups"
    
    def clear_celery_tasks(self, request, queryset):
        """Clear all running Celery tasks"""
        from celery import current_app
        
        try:
            # Get Celery app
            celery_app = current_app
            
            # Purge all tasks from all queues
            purged_count = 0
            
            # Get all active tasks
            active_tasks = celery_app.control.inspect().active()
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    if tasks:
                        purged_count += len(tasks)
                        # Revoke each task
                        for task in tasks:
                            celery_app.control.revoke(task['id'], terminate=True)
            
            # Purge all queues
            celery_app.control.purge()
            
            # Reset source configurations status
            for source in queryset:
                if source.status == 'CRAWLING':
                    source.status = 'PENDING'
                    source.save()
            
            self.message_user(request, f"Cleared {purged_count} active tasks and purged all queues")
            
        except Exception as e:
            self.message_user(request, f"Failed to clear Celery tasks: {e}", level='ERROR')
    clear_celery_tasks.short_description = "Clear Celery Tasks"
    
    def reset_flow(self, request, queryset):
        """Reset entire crawl flow"""
        from apps.lawyers.models import Lawyer
        
        reset_count = 0
        for source in queryset:
            # Reset source configuration
            source.status = 'PENDING'
            source.progress_percentage = 0.0
            source.total_urls = 0
            source.crawled_urls = 0
            source.success_count = 0
            source.error_count = 0
            source.save()
            
            # Reset related lawyers
            lawyers = Lawyer.objects.filter(source_url__in=source.start_urls)
            lawyers.update(
                is_detail_crawled=False,
                attorney_details='',
                detail_url=''
            )
            
            # Reset discovery URLs
            from apps.crawler.models import DiscoveryURL
            DiscoveryURL.objects.filter(source_config=source).update(
                status='PENDING',
                lawyers_found=0,
                error_message=''
            )
            
            reset_count += 1
            self.message_user(request, f"Reset flow for {source.name}")
        
        if reset_count > 0:
            self.message_user(request, f"Reset {reset_count} crawl flows")
        else:
            self.message_user(request, "No sources available to reset", level='WARNING')
    reset_flow.short_description = "Reset Flow"


@admin.register(DiscoveryURL)
class DiscoveryURLAdmin(admin.ModelAdmin):
    list_display = ['source_config', 'domain', 'practice_area', 'city', 'status', 'pagination_info', 'lawyers_found', 'created_at']
    list_filter = ['status', 'domain', 'practice_area', 'state', 'created_at']
    search_fields = ['url', 'domain', 'city', 'source_config__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'pagination_info']
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
    
    def pagination_info(self, obj):
        """Display pagination information"""
        if obj.total_pages > 1:
            return f"Page {obj.current_page}/{obj.total_pages}"
        else:
            return "Single page"
    pagination_info.short_description = "Pagination"




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
