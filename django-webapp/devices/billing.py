"""
Billing and subscription management logic.
"""
import logging
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

logger = logging.getLogger(__name__)


def create_subscription_plans():
    """Create default subscription plans if they don't exist"""
    plans_data = [
        {
            'name': 'Basic',
            'tier': 'basic',
            'price_monthly': Decimal('5.00'),
            'notification_limit': 100,
            'data_limit_mb': 1024,  # 1GB
            'features': ['Email notifications', 'Mobile app access', 'Basic support']
        },
        {
            'name': 'Plus',
            'tier': 'plus',
            'price_monthly': Decimal('10.00'),
            'notification_limit': 500,
            'data_limit_mb': 5120,  # 5GB
            'features': ['Email + SMS notifications', 'Mobile app access', 'Priority support', 'Advanced analytics']
        },
        {
            'name': 'Premium',
            'tier': 'premium',
            'price_monthly': Decimal('20.00'),
            'notification_limit': 0,  # Unlimited
            'data_limit_mb': 20480,  # 20GB
            'features': ['All notifications', 'Mobile app access', '24/7 support', 'Advanced analytics', 'API access']
        }
    ]
    
    from .subscription_models import SubscriptionPlan
    
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            tier=plan_data['tier'],
            defaults=plan_data
        )
        if created:
            logger.info(f"Created subscription plan: {plan.name}")
    
    return SubscriptionPlan.objects.all()


def create_trial_subscription(user, plan_tier='basic'):
    """Create a free trial subscription for new customer"""
    from .subscription_models import SubscriptionPlan, CustomerSubscription
    
    try:
        plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        # Create plans if they don't exist
        create_subscription_plans()
        plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
    
    # Check if subscription already exists
    if hasattr(user, 'subscription'):
        return user.subscription
    
    # Create trial subscription
    trial_start = timezone.now()
    trial_end = trial_start + timedelta(days=7)  # 7-day free trial
    
    subscription = CustomerSubscription.objects.create(
        user=user,
        plan=plan,
        status='trial',
        trial_start=trial_start,
        trial_end=trial_end,
        current_period_start=trial_start,
        current_period_end=trial_end
    )
    
    logger.info(f"Created trial subscription for {user.username}: {plan.name}")
    return subscription


def check_usage_limits(device, notification_data_bytes=0):
    """
    Check if device can send notification based on subscription limits.
    Returns (can_send, reason, usage_record)
    """
    from .subscription_models import DataUsage
    
    if not device.owner:
        return False, "Device not activated", None
    
    if not device.can_operate():
        return False, "Subscription not active", None
    
    try:
        subscription = device.owner.subscription
    except CustomerSubscription.DoesNotExist:
        return False, "No subscription found", None
    
    # Get or create current month usage
    now = timezone.now()
    usage, created = DataUsage.objects.get_or_create(
        device=device,
        subscription=subscription,
        year=now.year,
        month=now.month,
        defaults={
            'notification_limit': subscription.plan.notification_limit,
            'data_limit_mb': subscription.plan.data_limit_mb
        }
    )
    
    # Check notification limit
    if subscription.plan.notification_limit > 0:
        if usage.notification_count >= subscription.plan.notification_limit:
            return False, "Notification limit reached", usage
    
    # Check data limit
    if subscription.plan.data_limit_mb > 0:
        data_mb = Decimal(notification_data_bytes) / Decimal(1024 * 1024)
        if float(usage.data_used_mb) + float(data_mb) > subscription.plan.data_limit_mb:
            return False, "Data limit reached", usage
    
    return True, "OK", usage


def record_notification(device, data_bytes=0):
    """Record a notification and data usage"""
    from .subscription_models import DataUsage
    
    if not device.owner:
        return None
    
    try:
        subscription = device.owner.subscription
    except CustomerSubscription.DoesNotExist:
        return None
    
    now = timezone.now()
    usage, created = DataUsage.objects.get_or_create(
        device=device,
        subscription=subscription,
        year=now.year,
        month=now.month,
        defaults={
            'notification_limit': subscription.plan.notification_limit,
            'data_limit_mb': subscription.plan.data_limit_mb
        }
    )
    
    usage.add_notification(data_bytes)
    
    # Check for overage warnings
    if usage.is_near_limit and not usage.is_over_limit:
        # Send warning at 80%
        logger.warning(f"Device {device.serial_number} approaching limits: {usage.notification_usage_percent:.1f}% notifications, {usage.data_usage_percent:.1f}% data")
    
    return usage







