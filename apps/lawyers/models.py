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
    email = models.EmailField(blank=True)
    
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


class RocketReachLookup(models.Model):
    """Model to store RocketReach API lookup results"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
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
    rocketreach_id = models.CharField(max_length=100, blank=True)  # RocketReach person ID
    email = models.EmailField(blank=True)  # Found email
    phone = models.CharField(max_length=50, blank=True)  # Found phone
    linkedin_url = models.URLField(blank=True)  # LinkedIn profile
    twitter_url = models.URLField(blank=True)  # Twitter profile
    facebook_url = models.URLField(blank=True)  # Facebook profile
    
    # Professional information
    current_title = models.CharField(max_length=200, blank=True)  # Current job title
    current_company = models.CharField(max_length=300, blank=True)  # Current company
    location = models.CharField(max_length=200, blank=True)  # Location
    
    # Raw API response
    raw_response = models.JSONField(default=dict, blank=True)  # Full API response
    
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


