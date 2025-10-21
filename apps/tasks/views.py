from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ScheduledTask, TaskLog
from .serializers import ScheduledTaskSerializer, TaskLogSerializer
from .tasks import schedule_task


class TaskListView(generics.ListCreateAPIView):
    queryset = ScheduledTask.objects.all()
    serializer_class = ScheduledTaskSerializer


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ScheduledTask.objects.all()
    serializer_class = ScheduledTaskSerializer


class TaskLogListView(generics.ListAPIView):
    queryset = TaskLog.objects.all()
    serializer_class = TaskLogSerializer


@api_view(['POST'])
def ScheduleTaskView(request):
    """Schedule a new task"""
    serializer = ScheduledTaskSerializer(data=request.data)
    if serializer.is_valid():
        task = serializer.save()
        
        # Schedule the task
        schedule_task.delay(task.id)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
