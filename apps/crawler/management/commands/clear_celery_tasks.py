"""
Management command to clear all Celery tasks
"""

from django.core.management.base import BaseCommand
from celery import current_app
from apps.crawler.models import SourceConfiguration


class Command(BaseCommand):
    help = 'Clear all running Celery tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-sources',
            action='store_true',
            help='Reset source configurations status to PENDING',
        )

    def handle(self, *args, **options):
        try:
            # Get Celery app
            celery_app = current_app
            
            # Get all active tasks
            active_tasks = celery_app.control.inspect().active()
            purged_count = 0
            
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    if tasks:
                        purged_count += len(tasks)
                        self.stdout.write(f"Found {len(tasks)} active tasks on worker {worker}")
                        # Revoke each task
                        for task in tasks:
                            celery_app.control.revoke(task['id'], terminate=True)
                            self.stdout.write(f"Revoked task: {task['id']}")
            
            # Purge all queues
            celery_app.control.purge()
            
            # Reset source configurations if requested
            if options['reset_sources']:
                sources_reset = SourceConfiguration.objects.filter(status='CRAWLING')
                for source in sources_reset:
                    source.status = 'PENDING'
                    source.save()
                self.stdout.write(f"Reset {sources_reset.count()} source configurations to PENDING")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully cleared {purged_count} active tasks and purged all queues"
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to clear Celery tasks: {e}")
            )
