"""
Management command to create default subscription plans.
Run: python manage.py create_subscription_plans
"""
from django.core.management.base import BaseCommand
from devices.billing import create_subscription_plans


class Command(BaseCommand):
    help = 'Create default subscription plans (Basic, Plus, Premium)'

    def handle(self, *args, **options):
        self.stdout.write('Creating subscription plans...')
        plans = create_subscription_plans()
        
        for plan in plans:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[OK] {plan.name}: ${plan.price_monthly}/month - '
                    f'{plan.notification_limit if plan.notification_limit > 0 else "Unlimited"} notifications, '
                    f'{plan.data_limit_mb}MB data'
                )
            )
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {plans.count()} subscription plans'))

