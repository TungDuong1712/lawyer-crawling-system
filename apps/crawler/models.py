from django.db import models
from django.contrib.auth.models import User


class CrawlSession(models.Model):
    """Crawl session management"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Crawl parameters
    domains = models.JSONField(default=list)
    states = models.JSONField(default=list)
    practice_areas = models.JSONField(default=list)
    limit = models.IntegerField(default=10)
    
    # Results
    total_urls = models.IntegerField(default=0)
    crawled_urls = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Configuration
    delay_between_requests = models.FloatField(default=2.0)
    max_retries = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.status})"


class CrawlTask(models.Model):
    """Individual crawl tasks"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    session = models.ForeignKey(CrawlSession, on_delete=models.CASCADE, related_name='tasks')
    url = models.URLField(max_length=500)
    domain = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    practice_area = models.CharField(max_length=100)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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
    
    def __str__(self):
        return f"{self.domain} - {self.practice_area} - {self.city}"


class CrawlConfig(models.Model):
    """Crawl configuration templates"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    # Domain configurations
    domains_config = models.JSONField(default=dict)
    
    # Crawl settings
    delay_between_requests = models.FloatField(default=2.0)
    max_retries = models.IntegerField(default=3)
    timeout = models.IntegerField(default=30)
    user_agents = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name
