from django.contrib import admin
from .models import Lawyer, RocketReachLookup
from .rocketreach_tasks import lookup_lawyer_email_task


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'attorney_name', 'entity_type', 'city', 'state', 'domain', 'practice_area', 'email_count', 'entity_type']
    list_filter = ['entity_type', 'domain', 'state', 'practice_area', 'is_verified', 'is_active', 'crawl_timestamp']
    search_fields = ['company_name', 'attorney_name', 'phone', 'email', 'address']
    readonly_fields = ['crawl_timestamp', 'updated_at', 'completeness_score', 'quality_score', 'email_count', 'all_emails_display']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('source_url', 'domain', 'practice_area', 'state', 'city', 'entity_type')
        }),
        ('Lawyer Details', {
            'fields': ('company_name', 'attorney_name', 'phone', 'email', 'address', 'website')
        }),
        ('Multiple Emails', {
            'fields': ('company_emails', 'employee_contacts', 'all_emails_display'),
            'description': 'JSONField for storing multiple emails and employee contact information'
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
    
    actions = ['lookup_email_rocketreach', 'update_emails_from_rocketreach', 'add_company_email', 'view_all_emails']
    def email_count(self, obj):
        """Display total number of emails"""
        return len(obj.get_all_emails())
    email_count.short_description = 'Email Count'
    
    def all_emails_display(self, obj):
        """Display all emails in a formatted way"""
        emails = obj.get_all_emails()
        if not emails:
            return "No emails found"
        
        email_list = []
        for email in emails:
            email_list.append(f"• {email['email']} ({email['type']}) - {email.get('contact_name', 'N/A')}")
        
        return "\n".join(email_list)
    all_emails_display.short_description = 'All Emails'
    
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
    
    def add_company_email(self, request, queryset):
        """Add a company email to selected lawyers"""
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        
        if queryset.count() == 1:
            lawyer = queryset.first()
            # Redirect to a form to add email
            return HttpResponseRedirect(f"/admin/lawyers/lawyer/{lawyer.id}/add_email/")
        else:
            self.message_user(request, "Please select only one lawyer to add email", level='ERROR')
    add_company_email.short_description = "Add company email"
    
    def view_all_emails(self, request, queryset):
        """View all emails for selected lawyers"""
        email_summary = []
        for lawyer in queryset:
            emails = lawyer.get_all_emails()
            email_summary.append(f"\n{lawyer.company_name} ({len(emails)} emails):")
            for email in emails:
                email_summary.append(f"  • {email['email']} ({email['type']}) - {email.get('contact_name', 'N/A')}")
        
        self.message_user(request, "\n".join(email_summary))
    view_all_emails.short_description = "View all emails"


@admin.register(RocketReachLookup)
class RocketReachLookupAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'lookup_name', 'email', 'status', 'confidence_score', 'email_validation_status', 'lookup_timestamp']
    list_filter = ['status', 'lookup_timestamp', 'lawyer__domain', 'lawyer__entity_type', 'email_validation_status']
    search_fields = ['lawyer__company_name', 'lookup_name', 'email', 'current_company', 'contact_name']
    readonly_fields = ['lookup_timestamp', 'updated_at', 'api_credits_used', 'raw_response_display', 'raw_data_display', 'employee_emails_display']
    list_per_page = 50
    
    fieldsets = (
        ('Lookup Information', {
            'fields': ('lawyer', 'lookup_name', 'lookup_company', 'lookup_domain', 'status')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'linkedin_url', 'twitter_url', 'facebook_url')
        }),
        ('Professional Information', {
            'fields': ('current_title', 'current_company', 'location', 'birth_year')
        }),
        ('Additional Professional Data', {
            'fields': ('job_history', 'education', 'skills'),
            'description': 'JSONField data from RocketReach API'
        }),
        ('Employee Emails', {
            'fields': ('employee_emails_display',),
            'description': 'All employee emails found from company search'
        }),
        ('Location & Validation', {
            'fields': ('region_latitude', 'region_longitude', 'email_validation_status', 'phone_validation_status')
        }),
        ('API Information', {
            'fields': ('rocketreach_id', 'confidence_score', 'api_credits_used', 'api_request_id')
        }),
        ('Raw API Data', {
            'fields': ('raw_response_display', 'raw_data_display'),
            'description': 'Full API responses for debugging'
        }),
        ('Metadata', {
            'fields': ('lookup_timestamp', 'updated_at')
        })
    )
    
    actions = ['retry_failed_lookups', 'update_lawyer_emails']
    
    def raw_response_display(self, obj):
        """Display raw response in a formatted way"""
        if not obj.raw_response:
            return "No raw response data"
        
        import json
        try:
            # Display the original API response structure
            if isinstance(obj.raw_response, dict):
                # Check if it's a company employees response
                if 'profiles' in obj.raw_response and 'pagination' in obj.raw_response:
                    profiles = obj.raw_response.get('profiles', [])
                    pagination = obj.raw_response.get('pagination', {})
                    
                    summary = []
                    summary.append(f"🔍 Company Employees API Response:")
                    summary.append(f"   Total profiles: {len(profiles)} (API total: {pagination.get('total', 0)})")
                    summary.append(f"   Pagination: {pagination}")
                    
                    for i, profile in enumerate(profiles[:5]):  # Show first 5 employees
                        name = profile.get('name', 'N/A')
                        title = profile.get('current_title', 'N/A')
                        company = profile.get('current_employer', 'N/A')
                        location = profile.get('location', 'N/A')
                        status = profile.get('status', 'N/A')
                        summary.append(f"   {i+1}. {name} ({status}) - {title} at {company} ({location})")
                    
                    if len(profiles) > 5:
                        summary.append(f"   ... and {len(profiles) - 5} more profiles")
                    
                    return "\n".join(summary)
                
                # Check if it's a company search response
                elif 'companies' in obj.raw_response and 'pagination' in obj.raw_response:
                    companies = obj.raw_response.get('companies', [])
                    pagination = obj.raw_response.get('pagination', {})
                    
                    summary = []
                    summary.append(f"🏢 Company Search API Response:")
                    summary.append(f"   Total companies: {len(companies)} (API total: {pagination.get('total', 0)})")
                    
                    for i, company in enumerate(companies[:3]):  # Show first 3 companies
                        name = company.get('name', 'N/A')
                        domain = company.get('email_domain', 'N/A')
                        industry = company.get('industry_str', 'N/A')
                        summary.append(f"   {i+1}. {name} (Domain: {domain}, Industry: {industry})")
                    
                    return "\n".join(summary)
                
                # Check if it's a person search response (current format with 'profiles')
                elif 'profiles' in obj.raw_response:
                    profiles = obj.raw_response.get('profiles', [])
                    pagination = obj.raw_response.get('pagination', {})
                    summary = []
                    summary.append(f"👤 Person Search API Response:")
                    summary.append(f"   Total profiles: {len(profiles)} (API total: {pagination.get('total', 0)})")
                    
                    for i, profile in enumerate(profiles[:5]):  # Show first 5 profiles
                        name = profile.get('name', 'N/A')
                        title = profile.get('current_title', 'N/A')
                        company = profile.get('current_employer', 'N/A')
                        location = profile.get('location', 'N/A')
                        status = profile.get('status', 'N/A')
                        summary.append(f"   {i+1}. {name} - {title} at {company} ({location}) [{status}]")
                    
                    return "\n".join(summary)
                
                # Check if it's a person search response (new format with 'people')
                elif 'people' in obj.raw_response:
                    people = obj.raw_response.get('people', [])
                    pagination = obj.raw_response.get('pagination', {})
                    summary = []
                    summary.append(f"👤 Person Search API Response (New Format):")
                    summary.append(f"   Total people: {len(people)} (API total: {pagination.get('total', 0)})")
                    
                    for i, person in enumerate(people[:5]):  # Show first 5 people
                        name = person.get('name', 'N/A')
                        title = person.get('current_title', 'N/A')
                        company = person.get('current_employer', 'N/A')
                        location = person.get('location', 'N/A')
                        status = person.get('status', 'N/A')
                        summary.append(f"   {i+1}. {name} - {title} at {company} ({location}) [{status}]")
                    
                    return "\n".join(summary)
                
                # Fallback to JSON display for other response types
                else:
                    formatted = json.dumps(obj.raw_response, indent=2)
                    return formatted[:1000] + "..." if len(formatted) > 1000 else formatted
            else:
                # Fallback to JSON display for non-dict responses
                formatted = json.dumps(obj.raw_response, indent=2)
                return formatted[:1000] + "..." if len(formatted) > 1000 else formatted
        except Exception as e:
            return f"Error displaying raw response: {str(e)}"
    raw_response_display.short_description = 'Raw API Response'
    
    def raw_data_display(self, obj):
        """Display raw data in a formatted way"""
        if not obj.raw_data:
            return "No raw data"
        
        import json
        try:
            # Create a summary of the raw data
            summary = []
            
            # Company search results
            if 'company_search' in obj.raw_data:
                company_data = obj.raw_data['company_search']
                companies = company_data.get('companies', [])
                pagination = company_data.get('pagination', {})
                summary.append(f"Company Search: {len(companies)} companies found (total: {pagination.get('total', 0)})")
                
                for i, company in enumerate(companies[:3]):  # Show first 3 companies
                    summary.append(f"  {i+1}. {company.get('name', 'N/A')} (ID: {company.get('id', 'N/A')})")
            
            # Company lookup results
            if 'company_lookup' in obj.raw_data:
                company_lookup = obj.raw_data['company_lookup']
                company_name = company_lookup.get('name', 'N/A')
                company_domain = company_lookup.get('domain', 'N/A')
                industry = company_lookup.get('industry', 'N/A')
                summary.append(f"Company Lookup: {company_name} (Domain: {company_domain}, Industry: {industry})")
            
            # Employee search results
            if 'company_employees' in obj.raw_data:
                employee_data = obj.raw_data['company_employees']
                profiles = employee_data.get('profiles', [])
                pagination = employee_data.get('pagination', {})
                summary.append(f"Employee Search: {len(profiles)} employees found (total: {pagination.get('total', 0)})")
                
                for i, profile in enumerate(profiles[:5]):  # Show first 5 employees
                    summary.append(f"  {i+1}. {profile.get('name', 'N/A')} - {profile.get('current_title', 'N/A')}")
            
            # Person search results
            if 'person_search' in obj.raw_data:
                person_data = obj.raw_data['person_search']
                profiles = person_data.get('profiles', [])
                summary.append(f"Person Search: {len(profiles)} profiles found")
            
            return "\n".join(summary) if summary else "No data available"
        except Exception as e:
            return f"Error displaying raw data: {str(e)}"
    raw_data_display.short_description = 'Raw Data Summary'
    
    def employee_emails_display(self, obj):
        """Display employee emails in a formatted way"""
        if not obj.employee_emails:
            return "No employee emails found"
        
        try:
            summary = []
            for i, email_info in enumerate(obj.employee_emails[:15]):  # Show first 15
                name = email_info.get('name', 'N/A')
                title = email_info.get('title', 'N/A')
                email_domain = email_info.get('email_domain', 'N/A')
                email_type = email_info.get('email_type', 'N/A')
                confidence = email_info.get('confidence', 'unknown')
                note = email_info.get('note', '')
                full_emails = email_info.get('full_emails', [])
                
                # Add confidence indicator
                confidence_icon = "✅" if confidence == 'high' else "⚠️" if confidence == 'low' else "❓"
                
                # Format the line
                line = f"{i+1}. {confidence_icon} {name} ({title}) - {email_domain} ({email_type})"
                if full_emails:
                    line += f" 📧 {', '.join(full_emails)}"
                if note:
                    line += f" - {note}"
                
                summary.append(line)
            
            if len(obj.employee_emails) > 15:
                summary.append(f"... and {len(obj.employee_emails) - 15} more")
            
            # Add legend
            summary.append("\nLegend: ✅ High confidence | ⚠️ Low confidence | ❓ Unknown | 📧 Full email")
            
            return "\n".join(summary)
        except Exception as e:
            return f"Error displaying employee emails: {str(e)}"
    employee_emails_display.short_description = 'Employee Emails'
    
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
