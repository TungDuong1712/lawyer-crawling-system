from django.contrib import admin
from .models import Lawyer, RocketReachLookup
from .rocketreach_tasks import lookup_lawyer_email_task


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'attorney_name', 'entity_type', 'city', 'state', 'domain', 'practice_area', 'is_verified', 'completeness_score']
    list_filter = ['entity_type', 'domain', 'state', 'practice_area', 'is_verified', 'is_active', 'crawl_timestamp']
    search_fields = ['company_name', 'attorney_name', 'phone', 'email', 'address']
    readonly_fields = ['crawl_timestamp', 'updated_at', 'completeness_score', 'quality_score']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('source_url', 'domain', 'practice_area', 'state', 'city', 'entity_type')
        }),
        ('Lawyer Details', {
            'fields': ('company_name', 'attorney_name', 'phone', 'email', 'address', 'website')
        }),
        ('Professional Information', {
            'fields': ('practice_areas', 'attorney_details', 'law_school', 'bar_admissions', 'licensed_since', 'education')
        }),
        ('SuperLawyers Specific', {
            'fields': ('super_lawyer_years', 'super_lawyer_badge', 'rising_star', 'badges', 'sponsored')
        }),
        ('Additional Metadata', {
            'fields': ('image_url', 'profile_url', 'contact_url', 'firm_profile', 'office_locations')
        }),
        ('Lead Counsel (LawInfo)', {
            'fields': ('lead_counsel_attorneys', 'lead_counsel_images', 'lead_counsel_practice_areas', 'lead_counsel_years')
        }),
        ('Related Information', {
            'fields': ('related_cities', 'related_practice_areas')
        }),
        ('Crawling Information', {
            'fields': ('detail_url', 'is_detail_crawled', 'crawl_timestamp', 'updated_at', 'is_verified', 'is_active')
        }),
        ('Quality Scores', {
            'fields': ('completeness_score', 'quality_score')
        }),
    )
    
    actions = ['lookup_email_rocketreach', 'update_emails_from_rocketreach']
    
    def lookup_email_rocketreach(self, request, queryset):
        """Lookup emails using RocketReach API"""
        count = 0
        for lawyer in queryset:
            try:
                task = lookup_lawyer_email_task.delay(lawyer.id)
                count += 1
            except Exception as e:
                self.message_user(request, f"Failed to queue lookup for {lawyer.company_name}: {e}", level='ERROR')
        
        self.message_user(request, f"Queued {count} email lookups for RocketReach processing")
    lookup_email_rocketreach.short_description = "Lookup emails with RocketReach"
    
    def update_emails_from_rocketreach(self, request, queryset):
        """Update emails from successful RocketReach lookups"""
        updated_count = 0
        for lawyer in queryset:
            # Find successful RocketReach lookup
            lookup = RocketReachLookup.objects.filter(
                lawyer=lawyer,
                status='completed',
                email__isnull=False
            ).exclude(email='').first()
            
            if lookup and not lawyer.email:
                lawyer.email = lookup.email
                lawyer.save(update_fields=['email'])
                updated_count += 1
        
        self.message_user(request, f"Updated {updated_count} lawyer emails from RocketReach")
    update_emails_from_rocketreach.short_description = "Update emails from RocketReach"


@admin.register(RocketReachLookup)
class RocketReachLookupAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'lookup_name', 'email', 'status', 'confidence_score', 'lookup_timestamp']
    list_filter = ['status', 'lookup_timestamp', 'lawyer__domain', 'lawyer__entity_type']
    search_fields = ['lawyer__company_name', 'lookup_name', 'email', 'current_company']
    readonly_fields = ['lookup_timestamp', 'updated_at', 'api_credits_used']
    list_per_page = 50
    
    fieldsets = (
        ('Lookup Information', {
            'fields': ('lawyer', 'lookup_name', 'lookup_company', 'lookup_domain', 'status')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'linkedin_url', 'twitter_url', 'facebook_url')
        }),
        ('Professional Information', {
            'fields': ('current_title', 'current_company', 'location')
        }),
        ('API Information', {
            'fields': ('rocketreach_id', 'confidence_score', 'api_credits_used', 'api_request_id')
        }),
        ('Metadata', {
            'fields': ('lookup_timestamp', 'updated_at', 'raw_response')
        })
    )
    
    actions = ['retry_failed_lookups', 'update_lawyer_emails']
    
    def retry_failed_lookups(self, request, queryset):
        """Retry failed lookups"""
        count = 0
        for lookup in queryset.filter(status__in=['failed', 'not_found']):
            try:
                task = lookup_lawyer_email_task.delay(lookup.lawyer.id, force_refresh=True)
                count += 1
            except Exception as e:
                self.message_user(request, f"Failed to queue retry for {lookup.lawyer.company_name}: {e}", level='ERROR')
        
        self.message_user(request, f"Queued {count} retry lookups")
    retry_failed_lookups.short_description = "Retry failed lookups"
    
    def update_lawyer_emails(self, request, queryset):
        """Update lawyer emails from successful lookups"""
        updated_count = 0
        for lookup in queryset.filter(status='completed', email__isnull=False).exclude(email=''):
            if not lookup.lawyer.email:
                lookup.lawyer.email = lookup.email
                lookup.lawyer.save(update_fields=['email'])
                updated_count += 1
        
        self.message_user(request, f"Updated {updated_count} lawyer emails")
    update_lawyer_emails.short_description = "Update lawyer emails"
