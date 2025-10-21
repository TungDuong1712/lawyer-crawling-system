"""
URL configuration for lawyers_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/crawler/', include('apps.crawler.urls')),
    path('api/lawyers/', include('apps.lawyers.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('', include('apps.crawler.urls')),  # Main dashboard
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
