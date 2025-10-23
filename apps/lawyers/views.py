from django.shortcuts import render
from django.http import HttpResponse
from django.db import models
from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Lawyer
from .serializers import LawyerSerializer
from .filters import LawyerFilter
import csv
import json


class LawyerListView(generics.ListCreateAPIView):
    queryset = Lawyer.objects.filter(is_active=True)
    serializer_class = LawyerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LawyerFilter
    search_fields = ['company_name', 'phone', 'email', 'address']
    ordering_fields = ['company_name', 'crawl_timestamp', 'completeness_score']
    ordering = ['-crawl_timestamp']


class LawyerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lawyer.objects.all()
    serializer_class = LawyerSerializer


class LawyerSearchView(generics.ListAPIView):
    serializer_class = LawyerSerializer
    
    def get_queryset(self):
        queryset = Lawyer.objects.filter(is_active=True)
        
        # Search parameters
        domain = self.request.query_params.get('domain')
        state = self.request.query_params.get('state')
        practice_area = self.request.query_params.get('practice_area')
        city = self.request.query_params.get('city')
        search = self.request.query_params.get('search')
        
        if domain:
            queryset = queryset.filter(domain=domain)
        if state:
            queryset = queryset.filter(state=state)
        if practice_area:
            queryset = queryset.filter(practice_area=practice_area)
        if city:
            queryset = queryset.filter(city=city)
        if search:
            queryset = queryset.filter(company_name__icontains=search)
        
        return queryset


class LawyerExportView(generics.ListAPIView):
    serializer_class = LawyerSerializer
    
    def get_queryset(self):
        return Lawyer.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        format_type = request.query_params.get('format', 'csv')
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="lawyers.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Company Name', 'Phone', 'Email', 'Address', 'Website',
                'Domain', 'State', 'City', 'Practice Area', 'Crawl Date'
            ])
            
            for lawyer in queryset:
                writer.writerow([
                    lawyer.company_name,
                    lawyer.phone,
                    lawyer.email,
                    lawyer.address,
                    lawyer.website,
                    lawyer.domain,
                    lawyer.state,
                    lawyer.city,
                    lawyer.practice_area,
                    lawyer.crawl_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
        
        elif format_type == 'json':
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        return Response({'error': 'Invalid format'}, status=400)


@api_view(['GET'])
def LawyerStatsView(request):
    """Get lawyer statistics"""
    total_lawyers = Lawyer.objects.filter(is_active=True).count()
    by_domain = Lawyer.objects.filter(is_active=True).values('domain').distinct().count()
    by_state = Lawyer.objects.filter(is_active=True).values('state').distinct().count()
    
    # Top domains
    top_domains = Lawyer.objects.filter(is_active=True).values('domain').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]
    
    # Top states
    top_states = Lawyer.objects.filter(is_active=True).values('state').annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]
    
    # Quality metrics
    high_quality = Lawyer.objects.filter(is_active=True, completeness_score__gte=80).count()
    medium_quality = Lawyer.objects.filter(is_active=True, completeness_score__gte=50, completeness_score__lt=80).count()
    low_quality = Lawyer.objects.filter(is_active=True, completeness_score__lt=50).count()
    
    return Response({
        'total_lawyers': total_lawyers,
        'unique_domains': by_domain,
        'unique_states': by_state,
        'top_domains': list(top_domains),
        'top_states': list(top_states),
        'quality_metrics': {
            'high_quality': high_quality,
            'medium_quality': medium_quality,
            'low_quality': low_quality,
        }
    })
