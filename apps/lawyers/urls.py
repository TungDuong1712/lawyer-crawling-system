from django.urls import path
from . import views

app_name = 'lawyers'

urlpatterns = [
    path('', views.LawyerListView.as_view(), name='lawyer-list'),
    path('<int:pk>/', views.LawyerDetailView.as_view(), name='lawyer-detail'),
    path('search/', views.LawyerSearchView.as_view(), name='lawyer-search'),
    path('export/', views.LawyerExportView.as_view(), name='lawyer-export'),
    path('stats/', views.LawyerStatsView, name='lawyer-stats'),
]
