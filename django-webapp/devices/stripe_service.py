"""
Stripe payment integration for subscriptions.
"""
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def get_stripe_client():
    """Get Stripe client instance"""
    try:
        import stripe
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe.api_key:
            logger.warning("STRIPE_SECRET_KEY not configured")
            return None
        return stripe
    except ImportError:
        logger.warning("Stripe library not installed. Install with: pip install stripe")
        return None


def create_customer(user):
    """Create Stripe customer for user"""
    stripe = get_stripe_client()
    if not stripe:
        return None
    
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.get_full_name() or user.username,
            metadata={
                'user_id': user.id,
                'username': user.username
            }
        )
        return customer
    except Exception as e:
        logger.error(f"Failed to create Stripe customer: {str(e)}", exc_info=True)
        return None


def create_subscription(stripe_customer_id, plan_price_id, trial_days=7):
    """Create Stripe subscription"""
    stripe = get_stripe_client()
    if not stripe:
        return None
    
    try:
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{'price': plan_price_id}],
            trial_period_days=trial_days,
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
        )
        return subscription
    except Exception as e:
        logger.error(f"Failed to create Stripe subscription: {str(e)}", exc_info=True)
        return None


def update_subscription_payment_method(subscription_id, payment_method_id):
    """Update subscription payment method"""
    stripe = get_stripe_client()
    if not stripe:
        return None
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        stripe.Subscription.modify(
            subscription_id,
            default_payment_method=payment_method_id,
        )
        # Update all invoices to use this payment method
        stripe.Invoice.pay(subscription.latest_invoice, payment_method=payment_method_id)
        return True
    except Exception as e:
        logger.error(f"Failed to update payment method: {str(e)}", exc_info=True)
        return False


def cancel_subscription(stripe_subscription_id):
    """Cancel Stripe subscription"""
    stripe = get_stripe_client()
    if not stripe:
        return None
    
    try:
        subscription = stripe.Subscription.cancel(stripe_subscription_id)
        return subscription
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}", exc_info=True)
        return None


def handle_stripe_webhook(event):
    """Handle Stripe webhook events"""
    from .subscription_models import CustomerSubscription, PaymentHistory
    
    event_type = event['type']
    data = event['data']['object']
    
    try:
        if event_type == 'invoice.payment_succeeded':
            # Payment succeeded
            subscription_id = data.get('subscription')
            if subscription_id:
                try:
                    subscription = CustomerSubscription.objects.get(stripe_subscription_id=subscription_id)
                    subscription.activate()
                    
                    # Create payment record
                    PaymentHistory.objects.create(
                        subscription=subscription,
                        amount=Decimal(str(data['amount_paid'] / 100)),
                        status='succeeded',
                        stripe_invoice_id=data['id'],
                        stripe_payment_intent_id=data.get('payment_intent'),
                        paid_at=timezone.now(),
                        description=f"Monthly subscription - {subscription.plan.name}"
                    )
                    
                    logger.info(f"Payment succeeded for subscription {subscription_id}")
                except CustomerSubscription.DoesNotExist:
                    logger.warning(f"Subscription {subscription_id} not found")
        
        elif event_type == 'invoice.payment_failed':
            # Payment failed
            subscription_id = data.get('subscription')
            if subscription_id:
                try:
                    subscription = CustomerSubscription.objects.get(stripe_subscription_id=subscription_id)
                    subscription.suspend(grace_period_days=3)
                    
                    # Note: Devices will be suspended after grace period (handled by management command)
                    
                    # Create payment record
                    amount_due = data.get('amount_due', 0) or data.get('total', 0)
                    last_error = data.get('last_payment_error', {})
                    failure_reason = last_error.get('message', 'Payment failed') if last_error else 'Payment failed'
                    
                    PaymentHistory.objects.create(
                        subscription=subscription,
                        amount=Decimal(str(amount_due / 100)),
                        status='failed',
                        stripe_invoice_id=data['id'],
                        failure_reason=failure_reason,
                        description=f"Failed payment - {subscription.plan.name}"
                    )
                    
                    logger.warning(f"Payment failed for subscription {subscription_id}")
                except CustomerSubscription.DoesNotExist:
                    logger.warning(f"Subscription {subscription_id} not found")
        
        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled
            subscription_id = data['id']
            try:
                subscription = CustomerSubscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.cancel()
                logger.info(f"Subscription {subscription_id} cancelled")
            except CustomerSubscription.DoesNotExist:
                logger.warning(f"Subscription {subscription_id} not found")
        
        elif event_type == 'customer.subscription.updated':
            # Subscription updated
            subscription_id = data['id']
            try:
                subscription = CustomerSubscription.objects.get(stripe_subscription_id=subscription_id)
                # Update period dates
                subscription.current_period_start = timezone.datetime.fromtimestamp(
                    data['current_period_start'], tz=timezone.utc
                )
                subscription.current_period_end = timezone.datetime.fromtimestamp(
                    data['current_period_end'], tz=timezone.utc
                )
                subscription.save()
                logger.info(f"Subscription {subscription_id} updated")
            except CustomerSubscription.DoesNotExist:
                logger.warning(f"Subscription {subscription_id} not found")
    
    except Exception as e:
        logger.error(f"Error handling Stripe webhook {event_type}: {str(e)}", exc_info=True)
        raise

