from rest_framework import serializers
from .models import SourceConfiguration, DiscoveryURL


class SourceConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceConfiguration
        fields = '__all__'
        read_only_fields = ['created_at', 'started_at', 'completed_at']


class DiscoveryURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoveryURL
        fields = '__all__'
        read_only_fields = ['created_at', 'started_at', 'completed_at']
