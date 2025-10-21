from django.urls import path
from . import views

app_name = 'crawler'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('sessions/', views.CrawlSessionListCreateView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', views.CrawlSessionDetailView.as_view(), name='session-detail'),
    path('sessions/<int:pk>/start/', views.StartCrawlView, name='start-crawl'),
    path('sessions/<int:pk>/stop/', views.StopCrawlView, name='stop-crawl'),
    path('tasks/', views.CrawlTaskListView.as_view(), name='task-list'),
    path('configs/', views.CrawlConfigListView.as_view(), name='config-list'),
]
