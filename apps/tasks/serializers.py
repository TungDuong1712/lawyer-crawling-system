from rest_framework import serializers
from .models import ScheduledTask, TaskLog


class ScheduledTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledTask
        fields = '__all__'
        read_only_fields = ['created_at', 'started_at', 'completed_at']


class TaskLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskLog
        fields = '__all__'
        read_only_fields = ['timestamp']
