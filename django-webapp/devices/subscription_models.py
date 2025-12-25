"""
Subscription and billing models for Smart Mailbox system.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import decimal


class SubscriptionPlan(models.Model):
    """Subscription plan tiers"""
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('plus', 'Plus'),
        ('premium', 'Premium'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monthly price in USD")
    notification_limit = models.IntegerField(help_text="Monthly notification limit (0 = unlimited)")
    data_limit_mb = models.IntegerField(help_text="Monthly data limit in MB (0 = unlimited)")
    overage_notification_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=decimal.Decimal('0.10'),
        help_text="Price per notification over limit"
    )
    overage_data_price_per_mb = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=decimal.Decimal('0.01'),
        help_text="Price per MB over data limit"
    )
    features = models.JSONField(default=list, help_text="List of feature names")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['price_monthly']
    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"
    
    @property
    def is_unlimited_notifications(self):
        return self.notification_limit == 0
    
    @property
    def is_unlimited_data(self):
        return self.data_limit_mb == 0


class CustomerSubscription(models.Model):
    """Customer subscription to a plan"""
    STATUS_CHOICES = [
        ('trial', 'Free Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Billing
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Dates
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Grace period
    grace_period_end = models.DateTimeField(null=True, blank=True, help_text="End of grace period after failed payment")
    
    # Auto-renewal
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_in_trial(self):
        if not self.trial_end:
            return False
        return timezone.now() < self.trial_end and self.status == 'trial'
    
    @property
    def is_in_grace_period(self):
        if not self.grace_period_end:
            return False
        return timezone.now() < self.grace_period_end and self.status == 'suspended'
    
    @property
    def is_active(self):
        return self.status == 'active' or self.is_in_trial or self.is_in_grace_period
    
    @property
    def days_until_renewal(self):
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return max(0, delta.days)
        return 0
    
    def activate(self):
        """Activate subscription after trial or payment"""
        self.status = 'active'
        self.grace_period_end = None
        self.save()
    
    def suspend(self, grace_period_days=3):
        """Suspend subscription due to payment failure"""
        self.status = 'suspended'
        self.grace_period_end = timezone.now() + timedelta(days=grace_period_days)
        self.save()
    
    def cancel(self):
        """Cancel subscription"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        self.save()
    
    def renew_period(self):
        """Renew billing period"""
        self.current_period_start = timezone.now()
        self.current_period_end = self.current_period_start + timedelta(days=30)
        self.save()


class DataUsage(models.Model):
    """Track data usage per device per month"""
    device = models.ForeignKey('Device', on_delete=models.CASCADE, related_name='data_usage')
    subscription = models.ForeignKey(CustomerSubscription, on_delete=models.CASCADE, related_name='usage_records')
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    # Usage metrics
    notification_count = models.IntegerField(default=0, help_text="Number of mail detections/notifications")
    data_used_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Data used in MB")
    
    # Limits from plan
    notification_limit = models.IntegerField(help_text="Plan notification limit")
    data_limit_mb = models.IntegerField(help_text="Plan data limit in MB")
    
    # Overage
    overage_notifications = models.IntegerField(default=0)
    overage_data_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overage_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['device', 'year', 'month']
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['device', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.device.serial_number} - {self.year}/{self.month:02d}"
    
    @property
    def notification_usage_percent(self):
        if self.notification_limit == 0:
            return 0
        return (self.notification_count / self.notification_limit) * 100
    
    @property
    def data_usage_percent(self):
        if self.data_limit_mb == 0:
            return 0
        return (float(self.data_used_mb) / self.data_limit_mb) * 100
    
    @property
    def is_near_limit(self):
        """Check if usage is near limit (80% or more)"""
        return (self.notification_usage_percent >= 80 or self.data_usage_percent >= 80)
    
    @property
    def is_over_limit(self):
        """Check if usage exceeds limit"""
        return (self.notification_count > self.notification_limit and self.notification_limit > 0) or \
               (float(self.data_used_mb) > self.data_limit_mb and self.data_limit_mb > 0)
    
    def add_notification(self, data_bytes=0):
        """Add a notification and data usage"""
        self.notification_count += 1
        if data_bytes > 0:
            mb_used = decimal.Decimal(data_bytes) / decimal.Decimal(1024 * 1024)
            self.data_used_mb += mb_used
        
        # Calculate overage
        if self.notification_limit > 0 and self.notification_count > self.notification_limit:
            self.overage_notifications = self.notification_count - self.notification_limit
        
        if self.data_limit_mb > 0 and float(self.data_used_mb) > self.data_limit_mb:
            self.overage_data_mb = self.data_used_mb - decimal.Decimal(self.data_limit_mb)
        
        # Calculate overage charges
        self._calculate_overage_charge()
        self.save()
    
    def _calculate_overage_charge(self):
        """Calculate overage charges based on plan pricing"""
        plan = self.subscription.plan
        charge = decimal.Decimal('0.00')
        
        if self.overage_notifications > 0:
            charge += decimal.Decimal(self.overage_notifications) * plan.overage_notification_price
        
        if self.overage_data_mb > 0:
            charge += self.overage_data_mb * plan.overage_data_price_per_mb
        
        self.overage_charge = charge


class PaymentHistory(models.Model):
    """Payment transaction history"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    subscription = models.ForeignKey(CustomerSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in USD")
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata
    description = models.TextField(blank=True, help_text="Payment description")
    failure_reason = models.TextField(blank=True, help_text="Reason for failure if failed")
    
    # Dates
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.subscription.user.username} - ${self.amount} - {self.status}"







