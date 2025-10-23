from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('sessions/', views.SourceConfigurationListCreateView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', views.SourceConfigurationDetailView.as_view(), name='session-detail'),
    path('sessions/<int:pk>/start/', views.StartCrawlView, name='start-crawl'),
    path('sessions/<int:pk>/stop/', views.StopCrawlView, name='stop-crawl'),
    path('discovery-urls/', views.DiscoveryURLListView.as_view(), name='discovery-url-list'),
]
