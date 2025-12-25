"""
Management command to process monthly billing.
Run daily via cron: python manage.py process_billing
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from devices.subscription_models import CustomerSubscription, PaymentHistory
from devices.stripe_service import get_stripe_client
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process monthly billing for active subscriptions'

    def handle(self, *args, **options):
        self.stdout.write('Processing monthly billing...')
        
        stripe = get_stripe_client()
        if not stripe:
            self.stdout.write(self.style.ERROR('Stripe not configured'))
            return
        
        # Find subscriptions that need billing
        now = timezone.now()
        subscriptions = CustomerSubscription.objects.filter(
            status__in=['active', 'trial'],
            current_period_end__lte=now
        )
        
        processed = 0
        succeeded = 0
        failed = 0
        
        for subscription in subscriptions:
            processed += 1
            self.stdout.write(f'Processing subscription for {subscription.user.username}...')
            
            # Check if trial ended
            if subscription.status == 'trial' and subscription.trial_end and now >= subscription.trial_end:
                # Trial ended, need payment method
                if not subscription.stripe_payment_method_id:
                    self.stdout.write(
                        self.style.WARNING(f'  Trial ended for {subscription.user.username}, no payment method')
                    )
                    subscription.suspend()
                    failed += 1
                    continue
            
            # Process payment via Stripe
            try:
                # Create invoice
                invoice = stripe.Invoice.create(
                    customer=subscription.stripe_customer_id,
                    subscription=subscription.stripe_subscription_id,
                    auto_advance=True
                )
                
                # Pay invoice
                invoice = stripe.Invoice.pay(invoice.id)
                
                if invoice.status == 'paid':
                    # Payment succeeded
                    subscription.activate()
                    subscription.renew_period()
                    
                    # Create payment record
                    PaymentHistory.objects.create(
                        subscription=subscription,
                        amount=invoice.amount_paid / 100,
                        status='succeeded',
                        stripe_invoice_id=invoice.id,
                        stripe_payment_intent_id=invoice.payment_intent,
                        paid_at=timezone.now(),
                        description=f"Monthly subscription - {subscription.plan.name}"
                    )
                    
                    succeeded += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Payment succeeded for {subscription.user.username}')
                    )
                else:
                    # Payment failed
                    subscription.suspend(grace_period_days=3)
                    
                    PaymentHistory.objects.create(
                        subscription=subscription,
                        amount=invoice.amount_due / 100,
                        status='failed',
                        stripe_invoice_id=invoice.id,
                        failure_reason=invoice.last_payment_error.get('message', 'Payment failed') if invoice.last_payment_error else 'Payment failed',
                        description=f"Failed payment - {subscription.plan.name}"
                    )
                    
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ✗ Payment failed for {subscription.user.username}')
                    )
            
            except Exception as e:
                logger.error(f"Error processing billing for {subscription.user.username}: {str(e)}", exc_info=True)
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nBilling complete: {processed} processed, {succeeded} succeeded, {failed} failed'
            )
        )







