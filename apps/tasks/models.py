from django.db import models
from django.contrib.auth.models import User


class ScheduledTask(models.Model):
    """Scheduled task management"""
    TASK_TYPES = [
        ('crawl', 'Crawl Task'),
        ('export', 'Export Task'),
        ('cleanup', 'Cleanup Task'),
        ('quality_check', 'Quality Check'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Schedule
    scheduled_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Task configuration
    parameters = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Results
    result = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Celery task ID
    celery_task_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.task_type}) - {self.status}"


class TaskLog(models.Model):
    """Task execution logs"""
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.task.name} - {self.level} - {self.message[:50]}"
