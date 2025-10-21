from django.contrib import admin
from .models import Lawyer, LawyerReview, LawyerContact


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'city', 'state', 'domain', 'practice_area', 'is_verified', 'completeness_score']
    list_filter = ['domain', 'state', 'practice_area', 'is_verified', 'is_active', 'crawl_timestamp']
    search_fields = ['company_name', 'phone', 'email', 'address']
    readonly_fields = ['crawl_timestamp', 'updated_at']
    list_per_page = 50


@admin.register(LawyerReview)
class LawyerReviewAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'reviewer_name', 'rating', 'is_verified', 'created_at']
    list_filter = ['rating', 'is_verified', 'created_at']
    search_fields = ['lawyer__company_name', 'reviewer_name', 'review_text']


@admin.register(LawyerContact)
class LawyerContactAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'contact_method', 'status', 'contacted_by', 'contacted_at']
    list_filter = ['contact_method', 'status', 'contacted_at']
    search_fields = ['lawyer__company_name', 'contact_details', 'notes']
