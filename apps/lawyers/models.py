from django.db import models
from django.contrib.auth.models import User
import json


class Lawyer(models.Model):
    """Lawyer information model"""
    source_url = models.URLField(max_length=500)
    domain = models.CharField(max_length=100)
    practice_area = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    # Lawyer details
    company_name = models.CharField(max_length=300)
    attorney_name = models.CharField(max_length=200, blank=True)  # Individual attorney name
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    practice_areas = models.TextField(blank=True)
    attorney_details = models.TextField(blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)  # Primary email
    
    # Multiple emails support (for companies with multiple employees)
    company_emails = models.JSONField(default=list, blank=True)  # List of emails for company
    employee_contacts = models.JSONField(default=list, blank=True)  # List of employee contact info
    
    # Professional credentials
    law_school = models.CharField(max_length=200, blank=True)
    bar_admissions = models.TextField(blank=True)
    licensed_since = models.CharField(max_length=50, blank=True)
    education = models.TextField(blank=True)
    
    # SuperLawyers specific fields
    super_lawyer_years = models.CharField(max_length=100, blank=True)
    super_lawyer_badge = models.CharField(max_length=100, blank=True)
    rising_star = models.BooleanField(default=False)
    badges = models.TextField(blank=True)  # JSON string for multiple badges
    
    # Additional metadata
    image_url = models.URLField(blank=True)
    profile_url = models.URLField(blank=True)
    contact_url = models.URLField(blank=True)
    sponsored = models.BooleanField(default=False)
    
    # Office locations (for multi-location firms)
    office_locations = models.TextField(blank=True)  # JSON string for multiple locations
    
    # Lead Counsel information (LawInfo specific)
    lead_counsel_attorneys = models.TextField(blank=True)  # JSON string for multiple attorneys
    lead_counsel_images = models.TextField(blank=True)  # JSON string for multiple images
    lead_counsel_practice_areas = models.TextField(blank=True)  # JSON string for practice areas
    lead_counsel_years = models.TextField(blank=True)  # JSON string for years of experience
    
    # Related information
    related_cities = models.TextField(blank=True)  # JSON string for related cities
    related_practice_areas = models.TextField(blank=True)  # JSON string for related practice areas
    
    # Firm profile information
    firm_profile = models.URLField(blank=True)  # URL to firm profile page
    
    # Detail URL for second-stage crawling
    detail_url = models.URLField(max_length=500, blank=True)
    is_detail_crawled = models.BooleanField(default=False)
    
    # Metadata
    crawl_timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Entity type detection
    ENTITY_TYPE_CHOICES = [
        ('law_firm', 'Law Firm'),
        ('individual_attorney', 'Individual Attorney'),
        ('unknown', 'Unknown'),
    ]
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES, default='unknown')
    
    # Quality scores
    completeness_score = models.FloatField(default=0.0)
    quality_score = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-crawl_timestamp']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['state']),
            models.Index(fields=['practice_area']),
            models.Index(fields=['company_name']),
            models.Index(fields=['domain', 'state']),
            models.Index(fields=['practice_area', 'city']),
            models.Index(fields=['crawl_timestamp']),
            models.Index(fields=['completeness_score']),
            models.Index(fields=['quality_score']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.city}, {self.state}"
    
    def calculate_completeness_score(self):
        """Calculate completeness score based on available fields"""
        # Core fields (higher weight)
        core_fields = [
            self.company_name, self.attorney_name, self.phone, 
            self.address, self.website, self.email
        ]
        
        # Additional fields (lower weight)
        additional_fields = [
            self.practice_areas, self.attorney_details, self.law_school,
            self.bar_admissions, self.licensed_since, self.education
        ]
        
        # Calculate weighted score
        core_filled = sum(1 for field in core_fields if field)
        additional_filled = sum(1 for field in additional_fields if field)
        
        # Core fields worth 70%, additional fields worth 30%
        score = (core_filled / len(core_fields)) * 70 + (additional_filled / len(additional_fields)) * 30
        return min(score, 100)  # Cap at 100%
    
    def detect_entity_type(self):
        """Detect if this is a law firm or individual attorney based on domain and name patterns"""
        # Domain-based detection
        if self.domain == 'lawinfo.com':
            return 'law_firm'  # LawInfo primarily lists law firms
        elif self.domain == 'superlawyers.com':
            return 'individual_attorney'  # SuperLawyers primarily lists individual attorneys
        
        # Name-based detection for other domains
        if not self.company_name:
            return 'unknown'
        
        name_lower = self.company_name.lower()
        
        # Law firm indicators
        firm_indicators = [
            'law', 'firm', 'attorneys', 'p.c.', 'llp', 'llc', 'group', 'associates',
            'partners', 'legal', 'office', 'offices', '&', 'and', 'lawyers'
        ]
        
        # Individual attorney indicators
        individual_indicators = [
            'esq', 'esquire', 'attorney', 'lawyer', 'counsel', 'mr.', 'ms.', 'dr.'
        ]
        
        # Check for firm indicators
        for indicator in firm_indicators:
            if indicator in name_lower:
                return 'law_firm'
        
        # Check for individual indicators
        for indicator in individual_indicators:
            if indicator in name_lower:
                return 'individual_attorney'
        
        # Check if it's likely a personal name (no firm indicators, short name)
        if len(self.company_name.split()) <= 3 and not any(indicator in name_lower for indicator in firm_indicators):
            return 'individual_attorney'
        
        return 'unknown'

    def calculate_quality_score(self):
        """Calculate data quality score based on validation"""
        import re
        score = 0
        
        # Phone validation (US format)
        if self.phone and re.match(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$', self.phone):
            score += 25
        
        # Email validation
        if self.email and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            score += 25
        
        # Address validation (basic length check)
        if self.address and len(self.address) > 10:
            score += 25
        
        # Company name validation
        if self.company_name and len(self.company_name) > 3:
            score += 25
        
        return score
    
    def save(self, *args, **kwargs):
        """Override save to calculate scores and detect entity type"""
        # Auto-detect entity type if not set
        if self.entity_type == 'unknown':
            self.entity_type = self.detect_entity_type()
        
        # Update attorney_name based on entity type
        if self.entity_type == 'law_firm':
            # For law firms, attorney_name should be empty or "Multiple Attorneys"
            if not self.attorney_name:
                self.attorney_name = ''
        elif self.entity_type == 'individual_attorney':
            # For individual attorneys, attorney_name should match company_name
            if not self.attorney_name and self.company_name:
                self.attorney_name = self.company_name
        
        self.completeness_score = self.calculate_completeness_score()
        self.quality_score = self.calculate_quality_score()
        super().save(*args, **kwargs)
    
    def add_company_email(self, email, email_type='general', contact_name='', contact_title='', 
                          source='rocketreach', confidence_score=0.0):
        """Add a new email to the company using JSONField"""
        from datetime import datetime
        
        # Initialize company_emails if empty
        if not self.company_emails:
            self.company_emails = []
        
        # Check if email already exists
        for existing_email in self.company_emails:
            if existing_email.get('email') == email:
                return False
        
        # Add new email to JSONField
        new_email = {
            'email': email,
            'type': email_type,
            'contact_name': contact_name,
            'contact_title': contact_title,
            'source': source,
            'confidence': confidence_score,
            'verified': False,
            'created_at': datetime.now().isoformat()
        }
        
        self.company_emails.append(new_email)
        self.save(update_fields=['company_emails'])
        
        return new_email
    
    def get_all_emails(self):
        """Get all emails for this company/lawyer"""
        emails = []
        seen_emails = set()
        
        # Primary email (only if not already in company emails)
        if self.email and self.email not in seen_emails:
            emails.append({
                'email': self.email,
                'type': 'primary',
                'source': 'crawled',
                'verified': True,
                'contact_name': self.attorney_name or 'N/A',
                'contact_title': 'Attorney'
            })
            seen_emails.add(self.email)
        
        # Company emails from JSONField
        if self.company_emails:
            for company_email in self.company_emails:
                if company_email.get('email') not in seen_emails:
                    emails.append({
                        'email': company_email.get('email'),
                        'type': company_email.get('type', 'general'),
                        'source': company_email.get('source', 'unknown'),
                        'verified': company_email.get('verified', False),
                        'contact_name': company_email.get('contact_name', 'N/A'),
                        'contact_title': company_email.get('contact_title', 'N/A'),
                        'confidence': company_email.get('confidence', 0.0)
                    })
                    seen_emails.add(company_email.get('email'))
        
        return emails
    
    def get_verified_emails(self):
        """Get only verified emails"""
        return [email for email in self.get_all_emails() if email.get('verified', False)]
    
    def get_emails_by_type(self, email_type):
        """Get emails by type"""
        return [email for email in self.get_all_emails() if email.get('type') == email_type]
    
    def get_lawyer_employee_emails(self):
        """Get all emails specifically for lawyer employees"""
        return self.get_all_emails()
    
    def get_professional_emails(self):
        """Get professional emails for lawyer"""
        return self.get_emails_by_type('professional')
    
    def get_personal_emails(self):
        """Get personal emails for lawyer"""
        return self.get_emails_by_type('personal')
    
    def get_previous_emails(self):
        """Get previous work emails for lawyer"""
        return self.get_emails_by_type('previous')
    
    def get_best_contact_email(self):
        """Get the best contact email for the lawyer"""
        all_emails = self.get_all_emails()
        
        # Priority order: primary > professional > personal > previous
        priority_order = ['primary', 'professional', 'personal', 'previous']
        
        for priority in priority_order:
            for email in all_emails:
                if email.get('type') == priority:
                    return email
        
        # If no emails found, return None
        return None
    
    def get_contact_summary(self):
        """Get a summary of all contact information for the lawyer"""
        return {
            'lawyer_name': self.attorney_name,
            'company_name': self.company_name,
            'practice_area': self.practice_area,
            'location': f"{self.city}, {self.state}",
            'total_emails': len(self.get_all_emails()),
            'best_contact': self.get_best_contact_email(),
            'professional_emails': len(self.get_professional_emails()),
            'personal_emails': len(self.get_personal_emails()),
            'previous_emails': len(self.get_previous_emails())
        }


class RocketReachLookup(models.Model):
    """Model to store RocketReach API lookup results"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('found', 'Found'),
        ('failed', 'Failed'),
        ('not_found', 'Not Found'),
    ]
    
    # Related lawyer
    lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name='rocketreach_lookups')
    
    # Lookup parameters
    lookup_name = models.CharField(max_length=200)  # Name used for lookup
    lookup_company = models.CharField(max_length=300, blank=True)  # Company name used for lookup
    lookup_domain = models.CharField(max_length=100, blank=True)  # Domain used for lookup
    
    # API response data
    rocketreach_id = models.CharField(max_length=100, blank=True, null=True)  # RocketReach person ID
    email = models.EmailField(blank=True, null=True)  # Found email
    phone = models.CharField(max_length=50, blank=True, null=True)  # Found phone
    linkedin_url = models.URLField(blank=True, null=True)  # LinkedIn profile
    twitter_url = models.URLField(blank=True, null=True)  # Twitter profile
    facebook_url = models.URLField(blank=True, null=True)  # Facebook profile
    
    # Professional information
    current_title = models.CharField(max_length=200, blank=True, null=True)  # Current job title
    current_company = models.CharField(max_length=300, blank=True, null=True)  # Current company
    location = models.CharField(max_length=200, blank=True, null=True)  # Location
    
    # Additional professional data
    birth_year = models.IntegerField(null=True, blank=True)  # Birth year
    job_history = models.JSONField(default=list, blank=True)  # Complete work experience
    education = models.JSONField(default=list, blank=True)  # Academic background
    skills = models.JSONField(default=list, blank=True)  # Professional skills
    
    # Location coordinates
    region_latitude = models.FloatField(null=True, blank=True)  # Latitude
    region_longitude = models.FloatField(null=True, blank=True)  # Longitude
    
    # Email and phone validation
    email_validation_status = models.CharField(max_length=50, blank=True)  # Email validation status
    phone_validation_status = models.CharField(max_length=50, blank=True)  # Phone validation status
    
    # Employee emails from company search
    employee_emails = models.JSONField(default=list, blank=True)  # All employee emails found
    
    # Raw API response
    raw_response = models.JSONField(default=dict, blank=True)  # Full API response
    raw_data = models.JSONField(default=dict, blank=True)  # All raw API responses for debugging
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confidence_score = models.FloatField(default=0.0)  # Match confidence (0-100)
    lookup_timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # API usage tracking
    api_credits_used = models.IntegerField(default=0)  # Credits consumed for this lookup
    api_request_id = models.CharField(max_length=100, blank=True)  # RocketReach request ID
    
    class Meta:
        ordering = ['-lookup_timestamp']
        indexes = [
            models.Index(fields=['lawyer']),
            models.Index(fields=['status']),
            models.Index(fields=['lookup_timestamp']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"RocketReach Lookup for {self.lawyer.company_name} - {self.status}"
    
    def get_email_confidence(self):
        """Get email confidence level"""
        if not self.email:
            return "No email found"
        
        if self.confidence_score >= 90:
            return "High confidence"
        elif self.confidence_score >= 70:
            return "Medium confidence"
        else:
            return "Low confidence"
    
    def is_successful(self):
        """Check if lookup was successful"""
        return self.status == 'completed' and bool(self.email)
    
    def get_social_profiles(self):
        """Get all social media profiles"""
        profiles = {}
        if self.linkedin_url:
            profiles['linkedin'] = self.linkedin_url
        if self.twitter_url:
            profiles['twitter'] = self.twitter_url
        if self.facebook_url:
            profiles['facebook'] = self.facebook_url
        return profiles
    
    def update_lawyer_email(self):
        """Update the related lawyer's email if found"""
        if self.is_successful() and self.email:
            self.lawyer.email = self.email
            self.lawyer.save(update_fields=['email'])
            return True
        return False


class RocketReachContact(models.Model):
    """Model to store contact information from RocketReach pagination crawling"""

    # Primary contact information
    email = models.EmailField(unique=True, help_text="Primary email address")
    name = models.CharField(max_length=200, blank=True, help_text="Full name")
    company = models.CharField(max_length=300, blank=True, help_text="Company name")
    title = models.CharField(max_length=200, blank=True, help_text="Job title")

    # Contact details
    phone = models.CharField(max_length=50, blank=True, help_text="Phone number")
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn profile URL")
    twitter_url = models.URLField(blank=True, help_text="X/Twitter profile URL")
    location = models.CharField(max_length=200, blank=True, help_text="Location")
    profile_photo = models.URLField(blank=True, help_text="Profile photo URL")

    # Email information
    primary_email = models.EmailField(blank=True, help_text="Primary email address")
    secondary_email = models.EmailField(blank=True, help_text="Secondary email address")
    contact_grade = models.CharField(max_length=10, blank=True, help_text="Contact quality grade (A, B, C, etc.)")

    # Professional information
    industry = models.CharField(max_length=100, blank=True, help_text="Industry")
    company_size = models.CharField(max_length=50, blank=True, help_text="Company size")
    experience_years = models.IntegerField(null=True, blank=True, help_text="Years of experience")
    work_experience = models.JSONField(default=list, blank=True, help_text="Work experience history")
    education = models.JSONField(default=list, blank=True, help_text="Education history")
    skills = models.TextField(blank=True, help_text="Skills and expertise")

    # Crawling metadata
    source_url = models.URLField(help_text="RocketReach source URL")
    page_number = models.IntegerField(default=1, help_text="Page number where found")
    position_on_page = models.IntegerField(default=1, help_text="Position on the page")
    profile_id = models.CharField(max_length=50, blank=True, help_text="RocketReach profile ID")

    # Status and validation
    is_verified = models.BooleanField(default=False, help_text="Email verification status")
    confidence_score = models.FloatField(default=0.0, help_text="Confidence score (0-1)")
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('bounced', 'Bounced'),
            ('invalid', 'Invalid'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )

    # Additional data
    raw_data = models.JSONField(default=dict, blank=True, help_text="Raw scraped data")
    notes = models.TextField(blank=True, help_text="Additional notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.email}) - {self.company}"
    
    def get_contact_summary(self):
        """Get summary of contact information"""
        return {
            'email': self.email,
            'name': self.name,
            'company': self.company,
            'title': self.title,
            'phone': self.phone,
            'location': self.location,
            'status': self.status,
            'confidence': self.confidence_score,
            'verified': self.is_verified
        }
    
    def get_email_confidence(self):
        """Get email confidence level"""
        if not self.email:
            return "No email found"
        
        if self.confidence_score >= 90:
            return "High confidence"
        elif self.confidence_score >= 70:
            return "Medium confidence"
        else:
            return "Low confidence"
    
    def is_successful(self):
        """Check if lookup was successful"""
        return self.status == 'completed' and bool(self.email)
    
    def get_social_profiles(self):
        """Get all social media profiles"""
        profiles = {}
        if self.linkedin_url:
            profiles['linkedin'] = self.linkedin_url
        if self.twitter_url:
            profiles['twitter'] = self.twitter_url
        if self.facebook_url:
            profiles['facebook'] = self.facebook_url
        return profiles
    
    def update_lawyer_email(self):
        """Update the related lawyer's email if found"""
        if self.is_successful() and self.email:
            self.lawyer.email = self.email
            self.lawyer.save(update_fields=['email'])
            return True
        return False



