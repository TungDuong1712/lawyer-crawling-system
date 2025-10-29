from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Lawyer, RocketReachLookup, RocketReachContact
from .rocketreach_tasks import lookup_lawyer_email_task


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'attorney_name', 'entity_type', 'city', 'state', 'domain', 'practice_area', 'email_count', 'entity_type']
    list_filter = ['entity_type', 'domain', 'state', 'practice_area', 'is_verified', 'is_active', 'crawl_timestamp']
    search_fields = ['company_name', 'attorney_name', 'phone', 'email', 'address']
    readonly_fields = ['crawl_timestamp', 'updated_at', 'email_count', 'all_emails_display']
    list_per_page = 50
    
    # Make large text/json fields more compact in the form
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3})},
        models.JSONField: {'widget': Textarea(attrs={'rows': 6})},
    }
    
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
            'fields': ('law_school', 'bar_admissions', 'licensed_since')
        }),
        ('Additional Metadata', {
            'fields': ('image_url', 'profile_url', 'contact_url', 'firm_profile', 'office_locations')
        }),
        ('Crawling Information', {
            'fields': ('detail_url', 'is_detail_crawled', 'crawl_timestamp', 'updated_at', 'is_verified', 'is_active')
        }),
    )
    
    actions = ['lookup_email_rocketreach']
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
    


@admin.register(RocketReachLookup)
class RocketReachLookupAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'lookup_name', 'email', 'status', 'employee_emails_summary', 'lookup_timestamp']
    list_filter = ['status', 'lookup_timestamp', 'lawyer__domain', 'lawyer__entity_type', 'email_validation_status']
    search_fields = ['lawyer__company_name', 'lookup_name', 'email', 'current_company', 'contact_name']
    readonly_fields = ['lookup_timestamp', 'employee_emails_display']
    list_per_page = 50
    
    # Compact large text/json fields in this admin as well
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3})},
        models.JSONField: {'widget': Textarea(attrs={'rows': 6})},
    }
    
    fieldsets = (
        ('Lookup Information', {
            'fields': ('lawyer', 'status', 'lookup_timestamp')
        }),
        ('Email Information', {
            'fields': ('email', 'email_validation_status'),
            'description': 'Primary email found and its validation status'
        }),
        ('Employee Emails', {
            'fields': ('employee_emails_display',),
            'description': 'All employee emails found from company search'
        }),
        ('Professional Context', {
            'fields': ('current_title', 'current_company', 'linkedin_url'),
            'description': 'Professional context for the email'
        }),
        ('API Data', {
            'fields': ('rocketreach_id', 'raw_response'),
            'description': 'RocketReach API response containing email data'
        }),
    )
    
    actions = ['retry_failed_lookups', 'update_lawyer_emails', 'export_employee_emails']
    
    def employee_emails_display(self, obj):
        """Display employee emails in a formatted way"""
        if not obj.employee_emails:
            return "No employee emails found"
        
        try:
            summary = []
            summary.append("=" * 80)
            summary.append("📧 EMPLOYEE EMAILS DETAILS")
            summary.append("=" * 80)
            
            for i, email_info in enumerate(obj.employee_emails[:20]):  # Show first 20
                name = email_info.get('name', 'N/A')
                title = email_info.get('title', 'N/A')
                company = email_info.get('company', 'N/A')
                source = email_info.get('source', 'N/A')
                actual_emails = email_info.get('actual_emails', [])
                
                # Employee header
                summary.append(f"\n{i+1}. {name}")
                summary.append(f"   Title: {title}")
                summary.append(f"   Company: {company}")
                summary.append(f"   Source: {source}")
                
                # Emails for this employee
                if actual_emails:
                    summary.append(f"   📧 Emails ({len(actual_emails)}):")
                    for j, email_data in enumerate(actual_emails):
                        email = email_data.get('email', 'N/A')
                        email_type = email_data.get('type', 'N/A')
                        summary.append(f"      {j+1}. {email} ({email_type})")
                else:
                    summary.append(f"   📧 No emails found")
                
                summary.append("-" * 60)
            
            if len(obj.employee_emails) > 20:
                summary.append(f"\n... and {len(obj.employee_emails) - 20} more employees")
            
            # Footer
            summary.append("\n" + "=" * 80)
            
            return "\n".join(summary)
        except Exception as e:
            return f"Error displaying employee emails: {str(e)}"
    employee_emails_display.short_description = 'Employee Emails Details'
    
    def employee_emails_summary(self, obj):
        """Display employee emails summary for list view"""
        if not obj.employee_emails:
            return "No emails"
        
        try:
            total_employees = len(obj.employee_emails)
            total_emails = 0
            for email_info in obj.employee_emails:
                actual_emails = email_info.get('actual_emails', [])
                total_emails += len(actual_emails)
            return f"👥 {total_employees} employees | 📧 {total_emails} emails"
        except Exception as e:
            return f"Error: {str(e)}"
    employee_emails_summary.short_description = 'Employee Emails Summary'
    
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
    
    def export_employee_emails(self, request, queryset):
        """Export employee emails to CSV"""
        import csv
        import io
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_emails_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Lookup ID', 'Lawyer ID', 'Lawyer Name', 'Company Name',
            'Employee Name', 'Employee Title', 'Employee Company',
            'Email', 'Email Type', 'Grade', 'Valid', 'Confidence', 'Source'
        ])
        
        count = 0
        for lookup in queryset:
            if lookup.employee_emails:
                for email_info in lookup.employee_emails:
                    name = email_info.get('name', '')
                    title = email_info.get('title', '')
                    company = email_info.get('company', '')
                    confidence = email_info.get('confidence', '')
                    source = email_info.get('source', '')
                    actual_emails = email_info.get('actual_emails', [])
                    
                    for email_data in actual_emails:
                        writer.writerow([
                            lookup.id,
                            lookup.lawyer.id,
                            lookup.lawyer.attorney_name or lookup.lawyer.company_name,
                            lookup.lawyer.company_name,
                            name,
                            title,
                            company,
                            email_data.get('email', ''),
                            email_data.get('type', ''),
                            email_data.get('grade', ''),
                            email_data.get('smtp_valid', ''),
                            confidence,
                            source
                        ])
                        count += 1
        
        self.message_user(request, f"Exported {count} employee emails to CSV")
        return response
    export_employee_emails.short_description = "Export employee emails to CSV"


@admin.register(RocketReachContact)
class RocketReachContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'get_title_from_work_experience', 'title_category', 'primary_email', 'contact_grade', 'location']
    list_filter = ['title_category', 'contact_grade', 'status', 'is_verified', 'company', 'location']
    search_fields = ['name', 'company', 'primary_email', 'secondary_email', 'location']
    readonly_fields = ['work_experience_display', 'education_display', 'skills_display']
    list_per_page = 50
    
    # Compact large text/json fields
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3})},
        models.JSONField: {'widget': Textarea(attrs={'rows': 6})},
    }
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company', 'location')
        }),
        ('Contact Information', {
            'fields': ('primary_email', 'secondary_email', 'contact_grade', 'phone')
        }),
        ('Social Media & Profile', {
            'fields': ('linkedin_url', 'twitter_url', 'profile_photo')
        }),
        ('Professional Details', {
            'fields': ('work_experience_display', 'education_display', 'skills_display'),
            'description': 'Professional experience, education, and skills'
        }),
        ('Crawling Information', {
            'fields': ('source_url', 'page_number', 'position_on_page', 'profile_id'),
            'description': 'Information about where this contact was crawled'
        }),
    )
    
    actions = ['export_contacts_csv', 'mark_as_verified']
    
    def get_title_from_work_experience(self, obj):
        """Get title from first work experience entry"""
        if not obj.work_experience:
            return "N/A"
        
        try:
            import json
            if isinstance(obj.work_experience, str):
                work_exp_data = json.loads(obj.work_experience)
            else:
                work_exp_data = obj.work_experience
            
            if work_exp_data and len(work_exp_data) > 0:
                first_exp = work_exp_data[0]
                if isinstance(first_exp, dict):
                    return first_exp.get('title', 'N/A')
                else:
                    # If it's a string, try to extract title
                    # Format: "Title @ Company" or just "Title"
                    if ' @ ' in first_exp:
                        return first_exp.split(' @ ')[0]
                    else:
                        return first_exp
            return "N/A"
        except Exception as e:
            return "N/A"
    get_title_from_work_experience.short_description = 'Title'
    get_title_from_work_experience.admin_order_field = 'work_experience'
    
    def work_experience_display(self, obj):
        """Display work experience in a formatted way"""
        if not obj.work_experience:
            return "No work experience found"
        
        try:
            # Parse JSON if it's a string
            import json
            if isinstance(obj.work_experience, str):
                work_exp_data = json.loads(obj.work_experience)
            else:
                work_exp_data = obj.work_experience
            
            summary = []
            summary.append("=" * 80)
            summary.append("💼 WORK EXPERIENCE")
            summary.append("=" * 80)
            
            for i, exp in enumerate(work_exp_data[:10]):  # Show first 10
                if isinstance(exp, dict):
                    # If it's a dictionary, extract fields
                    title = exp.get('title', 'N/A')
                    company = exp.get('company', 'N/A')
                    duration = exp.get('duration', 'N/A')
                    description = exp.get('description', '')
                    
                    summary.append(f"\n{i+1}. {title} at {company}")
                    summary.append(f"   Duration: {duration}")
                    if description:
                        summary.append(f"   Description: {description}")
                else:
                    # If it's a string, display as is
                    summary.append(f"\n{i+1}. {exp}")
                
                summary.append("-" * 60)
            
            if len(work_exp_data) > 10:
                summary.append(f"\n... and {len(work_exp_data) - 10} more experiences")
            
            return "\n".join(summary)
        except Exception as e:
            return f"Error displaying work experience: {str(e)}"
    work_experience_display.short_description = 'Work Experience Details'
    
    def education_display(self, obj):
        """Display education in a formatted way"""
        if not obj.education:
            return "No education found"
        
        try:
            # Parse JSON if it's a string
            import json
            if isinstance(obj.education, str):
                edu_data = json.loads(obj.education)
            else:
                edu_data = obj.education
            
            summary = []
            summary.append("=" * 80)
            summary.append("🎓 EDUCATION")
            summary.append("=" * 80)
            
            for i, edu in enumerate(edu_data[:10]):  # Show first 10
                if isinstance(edu, dict):
                    # If it's a dictionary, extract fields
                    degree = edu.get('degree', 'N/A')
                    school = edu.get('school', 'N/A')
                    year = edu.get('year', 'N/A')
                    field = edu.get('field', '')
                    
                    summary.append(f"\n{i+1}. {degree}")
                    summary.append(f"   School: {school}")
                    summary.append(f"   Year: {year}")
                    if field:
                        summary.append(f"   Field: {field}")
                else:
                    # If it's a string, display as is
                    summary.append(f"\n{i+1}. {edu}")
                
                summary.append("-" * 60)
            
            if len(edu_data) > 10:
                summary.append(f"\n... and {len(edu_data) - 10} more education entries")
            
            return "\n".join(summary)
        except Exception as e:
            return f"Error displaying education: {str(e)}"
    education_display.short_description = 'Education Details'
    
    def skills_display(self, obj):
        """Display skills in a formatted way"""
        if not obj.skills:
            return "No skills found"
        
        try:
            # Split skills by common delimiters and format nicely
            skills_list = obj.skills.replace(',', '\n').replace(';', '\n').split('\n')
            skills_list = [skill.strip() for skill in skills_list if skill.strip()]
            
            if not skills_list:
                return "No skills found"
            
            summary = []
            summary.append("=" * 80)
            summary.append("🛠️ SKILLS")
            summary.append("=" * 80)
            
            # Display skills in columns
            for i in range(0, len(skills_list), 3):
                row_skills = skills_list[i:i+3]
                summary.append(" | ".join(f"{skill:<25}" for skill in row_skills))
            
            return "\n".join(summary)
        except Exception as e:
            return f"Error displaying skills: {str(e)}"
    skills_display.short_description = 'Skills Details'
    
    def export_contacts_csv(self, request, queryset):
        """Export contacts to CSV"""
        import csv
        import io
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rocketreach_contacts_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Company', 'Primary Email', 'Secondary Email', 
            'Contact Grade', 'Phone', 'Location', 'LinkedIn URL', 'Twitter URL',
            'Profile Photo', 'Work Experience Count', 'Education Count',
            'Skills', 'Status', 'Is Verified', 'Source URL'
        ])
        
        count = 0
        for contact in queryset:
            work_exp_count = len(contact.work_experience) if contact.work_experience else 0
            edu_count = len(contact.education) if contact.education else 0
            
            writer.writerow([
                contact.id,
                contact.name,
                contact.company,
                contact.primary_email,
                contact.secondary_email,
                contact.contact_grade,
                contact.phone,
                contact.location,
                contact.linkedin_url,
                contact.twitter_url,
                contact.profile_photo,
                work_exp_count,
                edu_count,
                contact.skills[:500] if contact.skills else '',  # Limit skills length
                contact.status,
                contact.is_verified,
                contact.source_url
            ])
            count += 1
        
        self.message_user(request, f"Exported {count} contacts to CSV")
        return response
    export_contacts_csv.short_description = "Export contacts to CSV"
    
    def mark_as_verified(self, request, queryset):
        """Mark selected contacts as verified (placeholder for future functionality)"""
        count = queryset.count()
        self.message_user(request, f"Marked {count} contacts as verified (placeholder action)")
    mark_as_verified.short_description = "Mark as verified"
