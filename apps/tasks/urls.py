from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task-list'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('schedule/', views.ScheduleTaskView, name='schedule-task'),
    path('logs/', views.TaskLogListView.as_view(), name='task-logs'),
]
