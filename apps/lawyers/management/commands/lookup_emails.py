"""
Management command to lookup emails using RocketReach API
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models
from apps.lawyers.models import Lawyer, RocketReachLookup
from apps.lawyers.rocketreach_api_service import RocketReachLookupService
from apps.lawyers.rocketreach_tasks import (
    lookup_lawyer_email_task,
    bulk_lookup_lawyers_task,
    lookup_lawyers_without_email_task,
    update_lawyer_emails_from_rocketreach_task,
    cleanup_failed_lookups_task
)


class Command(BaseCommand):
    help = "Lookup emails for lawyers using RocketReach API"

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            choices=['single', 'bulk', 'missing', 'update', 'cleanup'],
            default='missing',
            help='Lookup mode: single, bulk, missing, update, or cleanup'
        )
        parser.add_argument(
            '--lawyer-id',
            type=int,
            help='Lawyer ID for single lookup mode'
        )
        parser.add_argument(
            '--lawyer-ids',
            nargs='+',
            type=int,
            help='List of Lawyer IDs for bulk lookup mode'
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Filter by domain (e.g., lawinfo.com, superlawyers.com)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of lawyers to process (default: 100)'
        )
        parser.add_argument(
            '--force-refresh',
            action='store_true',
            help='Force new lookup even if previous exists'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run lookup asynchronously using Celery'
        )
        parser.add_argument(
            '--days-old',
            type=int,
            default=7,
            help='Days old for cleanup mode (default: 7)'
        )

    def handle(self, *args, **options):
        # Check API key
        if not hasattr(settings, 'ROCKETREACH_API_KEY') or not settings.ROCKETREACH_API_KEY:
            raise CommandError("ROCKETREACH_API_KEY not configured in settings")

        mode = options['mode']
        
        if mode == 'single':
            self.handle_single_lookup(options)
        elif mode == 'bulk':
            self.handle_bulk_lookup(options)
        elif mode == 'missing':
            self.handle_missing_emails(options)
        elif mode == 'update':
            self.handle_update_emails(options)
        elif mode == 'cleanup':
            self.handle_cleanup(options)

    def handle_single_lookup(self, options):
        """Handle single lawyer lookup"""
        lawyer_id = options.get('lawyer_id')
        if not lawyer_id:
            raise CommandError("--lawyer-id is required for single lookup mode")

        try:
            lawyer = Lawyer.objects.get(id=lawyer_id)
        except Lawyer.DoesNotExist:
            raise CommandError(f"Lawyer with ID {lawyer_id} not found")

        self.stdout.write(f"🔍 Looking up email for: {lawyer.company_name}")

        if options['async']:
            # Run asynchronously
            task = lookup_lawyer_email_task.delay(lawyer_id, options['force_refresh'])
            self.stdout.write(f"✅ Task queued with ID: {task.id}")
        else:
            # Run synchronously
            service = RocketReachLookupService()
            lookup = service.lookup_lawyer_email(lawyer, options['force_refresh'])
            
            if lookup:
                self.stdout.write(f"✅ Lookup completed: {lookup.status}")
                if lookup.email:
                    self.stdout.write(f"📧 Email found: {lookup.email}")
                    self.stdout.write(f"🎯 Confidence: {lookup.confidence_score}%")
                else:
                    self.stdout.write("❌ No email found")
            else:
                self.stdout.write("❌ Lookup failed")

    def handle_bulk_lookup(self, options):
        """Handle bulk lawyer lookup"""
        lawyer_ids = options.get('lawyer_ids')
        if not lawyer_ids:
            raise CommandError("--lawyer-ids is required for bulk lookup mode")

        self.stdout.write(f"🔍 Bulk lookup for {len(lawyer_ids)} lawyers")

        if options['async']:
            # Run asynchronously
            task = bulk_lookup_lawyers_task.delay(lawyer_ids, 10)
            self.stdout.write(f"✅ Task queued with ID: {task.id}")
        else:
            # Run synchronously
            lawyers = Lawyer.objects.filter(id__in=lawyer_ids)
            service = RocketReachLookupService()
            results = service.bulk_lookup_lawyers(lawyers, 10)
            
            successful = sum(1 for r in results if r.get('success', False))
            self.stdout.write(f"✅ Bulk lookup completed: {successful}/{len(results)} successful")

    def handle_missing_emails(self, options):
        """Handle lookup for lawyers without emails"""
        domain = options.get('domain')
        limit = options.get('limit', 100)

        # Get lawyers without email
        lawyers_query = Lawyer.objects.filter(
            models.Q(email__isnull=True) | models.Q(email='')
        )
        if domain:
            lawyers_query = lawyers_query.filter(domain=domain)
        
        lawyers = lawyers_query[:limit]
        count = lawyers.count()

        self.stdout.write(f"🔍 Found {count} lawyers without email addresses")
        if domain:
            self.stdout.write(f"🌐 Filtered by domain: {domain}")

        if count == 0:
            self.stdout.write("✅ No lawyers found without email addresses")
            return

        if options['async']:
            # Run asynchronously
            task = lookup_lawyers_without_email_task.delay(domain, limit)
            self.stdout.write(f"✅ Task queued with ID: {task.id}")
        else:
            # Run synchronously
            service = RocketReachLookupService()
            results = []
            
            for i, lawyer in enumerate(lawyers, 1):
                self.stdout.write(f"Processing {i}/{count}: {lawyer.company_name}")
                
                try:
                    lookup = service.lookup_lawyer_email(lawyer)
                    if lookup and lookup.is_successful():
                        self.stdout.write(f"  ✅ Email found: {lookup.email}")
                    else:
                        self.stdout.write(f"  ❌ No email found")
                except Exception as e:
                    self.stdout.write(f"  ❌ Error: {e}")
                
                results.append({
                    'lawyer_id': lawyer.id,
                    'lawyer_name': lawyer.company_name,
                    'success': lookup is not None and lookup.is_successful() if lookup else False
                })

            successful = sum(1 for r in results if r.get('success', False))
            self.stdout.write(f"✅ Lookup completed: {successful}/{len(results)} successful")

    def handle_update_emails(self, options):
        """Handle updating lawyer emails from successful lookups"""
        self.stdout.write("🔄 Updating lawyer emails from successful RocketReach lookups")

        if options['async']:
            # Run asynchronously
            task = update_lawyer_emails_from_rocketreach_task.delay()
            self.stdout.write(f"✅ Task queued with ID: {task.id}")
        else:
            # Run synchronously
            successful_lookups = RocketReachLookup.objects.filter(
                status='completed',
                email__isnull=False
            ).exclude(email='')
            
            updated_count = 0
            for lookup in successful_lookups:
                if not lookup.lawyer.email:
                    lookup.lawyer.email = lookup.email
                    lookup.lawyer.save(update_fields=['email'])
                    updated_count += 1
                    self.stdout.write(f"✅ Updated {lookup.lawyer.company_name}: {lookup.email}")
            
            self.stdout.write(f"✅ Updated {updated_count} lawyer emails")

    def handle_cleanup(self, options):
        """Handle cleanup of old failed lookups"""
        days_old = options.get('days_old', 7)
        self.stdout.write(f"🧹 Cleaning up failed lookups older than {days_old} days")

        if options['async']:
            # Run asynchronously
            task = cleanup_failed_lookups_task.delay(days_old)
            self.stdout.write(f"✅ Task queued with ID: {task.id}")
        else:
            # Run synchronously
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=days_old)
            old_failed_lookups = RocketReachLookup.objects.filter(
                status__in=['failed', 'not_found'],
                lookup_timestamp__lt=cutoff_date
            )
            
            count = old_failed_lookups.count()
            old_failed_lookups.delete()
            
            self.stdout.write(f"✅ Deleted {count} old failed lookups")

    def show_statistics(self):
        """Show RocketReach lookup statistics"""
        total_lawyers = Lawyer.objects.count()
        lawyers_with_email = Lawyer.objects.exclude(email__isnull=True).exclude(email='').count()
        lawyers_without_email = total_lawyers - lawyers_with_email
        
        total_lookups = RocketReachLookup.objects.count()
        successful_lookups = RocketReachLookup.objects.filter(status='completed').count()
        failed_lookups = RocketReachLookup.objects.filter(status__in=['failed', 'not_found']).count()
        
        self.stdout.write(f"\n📊 ROCKETREACH STATISTICS:")
        self.stdout.write(f"Total lawyers: {total_lawyers}")
        self.stdout.write(f"Lawyers with email: {lawyers_with_email}")
        self.stdout.write(f"Lawyers without email: {lawyers_without_email}")
        self.stdout.write(f"Total lookups: {total_lookups}")
        self.stdout.write(f"Successful lookups: {successful_lookups}")
        self.stdout.write(f"Failed lookups: {failed_lookups}")
        
        if total_lookups > 0:
            success_rate = (successful_lookups / total_lookups) * 100
            self.stdout.write(f"Success rate: {success_rate:.1f}%")
