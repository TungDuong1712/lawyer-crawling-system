from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import SourceConfiguration, DiscoveryURL
from .serializers import SourceConfigurationSerializer, DiscoveryURLSerializer
from .tasks import crawl_session_task


class DashboardView(TemplateView):
    template_name = 'crawler/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_sessions'] = SourceConfiguration.objects.count()
        context['active_sessions'] = SourceConfiguration.objects.filter(status='running').count()
        context['total_lawyers'] = 0  # Will be calculated from lawyers app
        return context


class SourceConfigurationListCreateView(generics.ListCreateAPIView):
    queryset = SourceConfiguration.objects.all()
    serializer_class = SourceConfigurationSerializer


class SourceConfigurationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SourceConfiguration.objects.all()
    serializer_class = SourceConfigurationSerializer


class DiscoveryURLListView(generics.ListAPIView):
    queryset = DiscoveryURL.objects.all()
    serializer_class = DiscoveryURLSerializer


@api_view(['POST'])
def StartCrawlView(request, pk):
    """Start a crawl session"""
    try:
        session = SourceConfiguration.objects.get(pk=pk)
        if session.status != 'pending':
            return Response({'error': 'Session is not in pending status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Start crawl task
        task = crawl_session_task.delay(session.id)
        session.status = 'running'
        session.started_at = timezone.now()
        session.save()
        
        return Response({'message': 'Crawl session started', 'task_id': task.id})
    except SourceConfiguration.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def StopCrawlView(request, pk):
    """Stop a crawl session"""
    try:
        session = SourceConfiguration.objects.get(pk=pk)
        if session.status != 'running':
            return Response({'error': 'Session is not running'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        session.status = 'cancelled'
        session.completed_at = timezone.now()
        session.save()
        
        return Response({'message': 'Crawl session stopped'})
    except SourceConfiguration.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
