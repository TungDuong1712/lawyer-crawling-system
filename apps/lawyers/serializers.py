from rest_framework import serializers
from .models import Lawyer, LawyerReview, LawyerContact


class LawyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lawyer
        fields = '__all__'
        read_only_fields = ['crawl_timestamp', 'updated_at', 'completeness_score', 'quality_score']


class LawyerReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerReview
        fields = '__all__'
        read_only_fields = ['created_at']


class LawyerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = LawyerContact
        fields = '__all__'
        read_only_fields = ['created_at', 'contacted_at']
