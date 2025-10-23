from rest_framework import serializers
from .models import Lawyer


class LawyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lawyer
        fields = '__all__'
        read_only_fields = ['crawl_timestamp', 'updated_at', 'completeness_score', 'quality_score']
