from rest_framework import serializers
from .models import CrawlSession, CrawlTask, CrawlConfig


class CrawlSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlSession
        fields = '__all__'
        read_only_fields = ['created_at', 'started_at', 'completed_at']


class CrawlTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlTask
        fields = '__all__'
        read_only_fields = ['created_at', 'started_at', 'completed_at']


class CrawlConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
