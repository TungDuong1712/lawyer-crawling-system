import django_filters
from .models import Lawyer


class LawyerFilter(django_filters.FilterSet):
    domain = django_filters.CharFilter(field_name='domain', lookup_expr='icontains')
    state = django_filters.CharFilter(field_name='state', lookup_expr='icontains')
    city = django_filters.CharFilter(field_name='city', lookup_expr='icontains')
    practice_area = django_filters.CharFilter(field_name='practice_area', lookup_expr='icontains')
    company_name = django_filters.CharFilter(field_name='company_name', lookup_expr='icontains')
    has_phone = django_filters.BooleanFilter(field_name='phone', lookup_expr='isnull', exclude=True)
    has_email = django_filters.BooleanFilter(field_name='email', lookup_expr='isnull', exclude=True)
    has_website = django_filters.BooleanFilter(field_name='website', lookup_expr='isnull', exclude=True)
    is_verified = django_filters.BooleanFilter(field_name='is_verified')
    min_completeness = django_filters.NumberFilter(field_name='completeness_score', lookup_expr='gte')
    max_completeness = django_filters.NumberFilter(field_name='completeness_score', lookup_expr='lte')
    
    class Meta:
        model = Lawyer
        fields = ['domain', 'state', 'city', 'practice_area', 'company_name', 
                 'has_phone', 'has_email', 'has_website', 'is_verified',
                 'min_completeness', 'max_completeness']
