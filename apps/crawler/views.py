from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CrawlSession, CrawlTask, CrawlConfig
from .serializers import CrawlSessionSerializer, CrawlTaskSerializer, CrawlConfigSerializer
from .tasks import start_crawl_session


class DashboardView(TemplateView):
    template_name = 'crawler/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_sessions'] = CrawlSession.objects.count()
        context['active_sessions'] = CrawlSession.objects.filter(status='running').count()
        context['total_lawyers'] = 0  # Will be calculated from lawyers app
        return context


class CrawlSessionListCreateView(generics.ListCreateAPIView):
    queryset = CrawlSession.objects.all()
    serializer_class = CrawlSessionSerializer


class CrawlSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CrawlSession.objects.all()
    serializer_class = CrawlSessionSerializer


class CrawlTaskListView(generics.ListAPIView):
    queryset = CrawlTask.objects.all()
    serializer_class = CrawlTaskSerializer


class CrawlConfigListView(generics.ListCreateAPIView):
    queryset = CrawlConfig.objects.all()
    serializer_class = CrawlConfigSerializer


@api_view(['POST'])
def StartCrawlView(request, pk):
    """Start a crawl session"""
    try:
        session = CrawlSession.objects.get(pk=pk)
        if session.status != 'pending':
            return Response({'error': 'Session is not in pending status'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Start crawl task
        task = start_crawl_session.delay(session.id)
        session.status = 'running'
        session.started_at = timezone.now()
        session.save()
        
        return Response({'message': 'Crawl session started', 'task_id': task.id})
    except CrawlSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def StopCrawlView(request, pk):
    """Stop a crawl session"""
    try:
        session = CrawlSession.objects.get(pk=pk)
        if session.status != 'running':
            return Response({'error': 'Session is not running'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        session.status = 'cancelled'
        session.completed_at = timezone.now()
        session.save()
        
        return Response({'message': 'Crawl session stopped'})
    except CrawlSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
