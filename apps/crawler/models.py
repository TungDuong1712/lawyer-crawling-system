from django.db import models
from django.contrib.auth.models import User


class SourceConfiguration(models.Model):
    """Source configuration for lawyer crawling with start URLs and selectors"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CRAWLING', 'Crawling'),
        ('PAUSED', 'Paused'),
        ('RETRYING', 'Retrying After Error'),
        ('FAILED', 'Failed'),
        ('DONE', 'Done'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Start URLs - list of URLs to crawl
    start_urls = models.JSONField(
        default=list,
        help_text="List of start URLs to crawl, e.g., ['www.lawinfo.com/personal-injury/arizona/chandler/', 'www.lawinfo.com/personal-injury/new-mexico/albuquerque/']"
    )
    
    # Selectors - JSON field storing XPath selectors for data extraction
    selectors = models.JSONField(
        default=dict,
        help_text="JSON field storing XPath selectors for different data fields"
    )
    
    # Results
    total_urls = models.IntegerField(default=0)
    crawled_urls = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    delay_between_requests = models.FloatField(default=2.0)
    max_retries = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Source Configuration'
        verbose_name_plural = 'Source Configurations'
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class DiscoveryURL(models.Model):
    """Discovery URLs generated from source configuration"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('RETRYING', 'Retrying'),
    ]
    
    source_config = models.ForeignKey(SourceConfiguration, on_delete=models.CASCADE, related_name='discovery_urls')
    url = models.URLField(max_length=500)
    domain = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    practice_area = models.CharField(max_length=100)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    lawyers_found = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Celery task ID
    celery_task_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Discovery URL'
        verbose_name_plural = 'Discovery URLs'
    
    def __str__(self):
        return f"{self.domain} - {self.practice_area} - {self.city}"


