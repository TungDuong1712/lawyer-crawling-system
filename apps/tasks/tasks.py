from celery import shared_task
from django.utils import timezone
from .models import ScheduledTask, TaskLog
from apps.lawyers.tasks import calculate_quality_scores, cleanup_duplicate_lawyers, export_lawyers_data


@shared_task
def schedule_task(task_id):
    """Execute a scheduled task"""
    try:
        task = ScheduledTask.objects.get(id=task_id)
        task.status = 'running'
        task.started_at = timezone.now()
        task.save()
        
        # Log task start
        TaskLog.objects.create(
            task=task,
            level='info',
            message=f"Task {task.name} started"
        )
        
        # Execute based on task type
        if task.task_type == 'quality_check':
            result = calculate_quality_scores.delay()
            task.result = f"Quality check scheduled: {result.id}"
            
        elif task.task_type == 'cleanup':
            result = cleanup_duplicate_lawyers.delay()
            task.result = f"Cleanup scheduled: {result.id}"
            
        elif task.task_type == 'export':
            format_type = task.parameters.get('format', 'csv')
            result = export_lawyers_data.delay(format_type)
            task.result = f"Export scheduled: {result.id}"
            
        else:
            task.result = "Unknown task type"
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        # Log task completion
        TaskLog.objects.create(
            task=task,
            level='info',
            message=f"Task {task.name} completed successfully"
        )
        
        return f"Task {task_id} completed"
        
    except ScheduledTask.DoesNotExist:
        return f"Task {task_id} not found"
    except Exception as e:
        task.status = 'failed'
        task.error_message = str(e)
        task.completed_at = timezone.now()
        task.save()
        
        # Log task error
        TaskLog.objects.create(
            task=task,
            level='error',
            message=f"Task {task.name} failed: {str(e)}"
        )
        
        return f"Task {task_id} failed: {str(e)}"
