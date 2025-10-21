from django.db import models
from django.contrib.auth.models import User


class Lawyer(models.Model):
    """Lawyer information model"""
    source_url = models.URLField(max_length=500)
    domain = models.CharField(max_length=100)
    practice_area = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    # Lawyer details
    company_name = models.CharField(max_length=300)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    practice_areas = models.TextField(blank=True)
    attorney_details = models.TextField(blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    
    # Metadata
    crawl_timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
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
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.city}, {self.state}"
    
    def calculate_completeness_score(self):
        """Calculate completeness score based on available fields"""
        fields = [
            self.company_name, self.phone, self.address, 
            self.practice_areas, self.website, self.email
        ]
        filled_fields = sum(1 for field in fields if field)
        return (filled_fields / len(fields)) * 100


class LawyerReview(models.Model):
    """Lawyer reviews and ratings"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=200)
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.lawyer.company_name} - {self.rating} stars"


class LawyerContact(models.Model):
    """Lawyer contact attempts and results"""
    CONTACT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('contacted', 'Contacted'),
        ('responded', 'Responded'),
        ('not_interested', 'Not Interested'),
        ('invalid', 'Invalid Contact'),
    ]
    
    lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name='contacts')
    contact_method = models.CharField(max_length=50)  # email, phone, website
    contact_details = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=CONTACT_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    contacted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.lawyer.company_name} - {self.contact_method} - {self.status}"
