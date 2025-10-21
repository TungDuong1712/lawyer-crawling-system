from django.contrib import admin
from .models import CrawlSession, CrawlTask, CrawlConfig


@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'created_at', 'total_urls', 'crawled_urls']
    list_filter = ['status', 'created_at', 'domains']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(CrawlTask)
class CrawlTaskAdmin(admin.ModelAdmin):
    list_display = ['session', 'domain', 'practice_area', 'city', 'status', 'lawyers_found']
    list_filter = ['status', 'domain', 'practice_area', 'state']
    search_fields = ['url', 'domain', 'city']


@admin.register(CrawlConfig)
class CrawlConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'description']
