"""
Management command to check and suspend devices after grace period.
Run daily via cron: python manage.py check_suspended_devices
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from devices.models import Device
from devices.subscription_models import CustomerSubscription
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check suspended subscriptions and suspend devices after grace period'

    def handle(self, *args, **options):
        self.stdout.write('Checking suspended subscriptions...')
        
        now = timezone.now()
        
        # Find subscriptions in grace period that have expired
        expired_subscriptions = CustomerSubscription.objects.filter(
            status='suspended',
            grace_period_end__lte=now
        )
        
        suspended_count = 0
        
        for subscription in expired_subscriptions:
            # Suspend all devices for this user
            devices = Device.objects.filter(owner=subscription.user, lifecycle_state='active_subscription')
            
            for device in devices:
                device.suspend()
                suspended_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Suspended device {device.serial_number} for {subscription.user.username}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuspended {suspended_count} device(s) after grace period')
        )







