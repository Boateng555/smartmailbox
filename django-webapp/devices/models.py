from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time
import json


class Device(models.Model):
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('maintenance', 'Maintenance'),
    ]
    
    TRIGGER_TYPE_CHOICES = [
        ('automatic', 'Automatic (Timer)'),
        ('manual', 'Manual (User Request)'),
    ]
    
    CONNECTION_TYPE_CHOICES = [
        ('wifi', 'WiFi'),
        ('cellular', 'Cellular'),
        ('unknown', 'Unknown'),
    ]
    
    # Device lifecycle states
    LIFECYCLE_STATE_CHOICES = [
        ('pre_activation', 'Pre-Activation'),
        ('active_subscription', 'Active Subscription'),
        ('suspended', 'Suspended'),
        ('returned', 'Returned'),
        ('decommissioned', 'Decommissioned'),
    ]
    
    POWER_STATE_CHOICES = [
        ('sleep', 'Sleep'),
        ('awake', 'Awake'),
        ('uploading', 'Uploading'),
        ('charging', 'Charging'),
    ]
    
    serial_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    lifecycle_state = models.CharField(
        max_length=20,
        choices=LIFECYCLE_STATE_CHOICES,
        default='pre_activation',
        help_text="Device lifecycle state"
    )
    power_state = models.CharField(
        max_length=20,
        choices=POWER_STATE_CHOICES,
        default='sleep',
        help_text="Current power state"
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', null=True, blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    connection_type = models.CharField(
        max_length=20,
        choices=CONNECTION_TYPE_CHOICES,
        default='unknown',
        help_text="Current connection type (WiFi or Cellular)"
    )
    
    # Device metadata
    name = models.CharField(max_length=100, blank=True, help_text="Customer-assigned device name")
    location = models.CharField(max_length=200, blank=True, help_text="Device location description")
    battery_percentage = models.IntegerField(null=True, blank=True, help_text="Battery percentage (0-100)")
    firmware_version = models.CharField(max_length=50, blank=True, help_text="Current firmware version")
    
    # Activation
    activated_at = models.DateTimeField(null=True, blank=True, help_text="When device was activated by customer")
    claimed_at = models.DateTimeField(null=True, blank=True, help_text="When device was claimed")
    
    class Meta:
        ordering = ['-last_seen']
    
    def __str__(self):
        return f"{self.serial_number} ({self.status})"
    
    def can_operate(self):
        """Check if device can operate (has active subscription)"""
        if not self.owner:
            return False
        
        if self.lifecycle_state != 'active_subscription':
            return False
        
        # Check subscription status
        try:
            subscription = self.owner.subscription
            return subscription.is_active
        except CustomerSubscription.DoesNotExist:
            return False
    
    def activate(self, user):
        """Activate device for customer"""
        self.owner = user
        self.lifecycle_state = 'active_subscription'
        self.activated_at = timezone.now()
        self.claimed_at = timezone.now()
        self.save()
    
    def suspend(self):
        """Suspend device due to payment failure"""
        self.lifecycle_state = 'suspended'
        self.save()
    
    def resume(self):
        """Resume device after payment restored"""
        if self.owner:
            self.lifecycle_state = 'active_subscription'
            self.save()
    
    def decommission(self):
        """Decommission device (end of life)"""
        self.lifecycle_state = 'decommissioned'
        self.status = 'offline'
        self.save()


class SIM(models.Model):
    """SIM card model for tracking cellular data usage"""
    iccid = models.CharField(max_length=20, unique=True, help_text="SIM card ICCID")
    device = models.ForeignKey('Device', on_delete=models.CASCADE, related_name='sim_cards', null=True, blank=True)
    plan_mb = models.IntegerField(default=0, help_text="Data plan limit in MB")
    data_used_mb = models.FloatField(default=0.0, help_text="Data used in MB")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SIM Card"
        verbose_name_plural = "SIM Cards"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"SIM {self.iccid} ({self.data_used_mb:.2f}/{self.plan_mb} MB)"
    
    @property
    def data_used_percent(self):
        """Calculate percentage of data used"""
        if self.plan_mb == 0:
            return 0
        return (self.data_used_mb / self.plan_mb) * 100
    
    @property
    def is_near_limit(self):
        """Check if data usage is near limit (80% or more)"""
        return self.data_used_percent >= 80
    
    @property
    def is_over_limit(self):
        """Check if data usage exceeds limit"""
        return self.data_used_mb >= self.plan_mb
    
    def add_data_usage(self, bytes_used):
        """Add data usage in bytes"""
        mb_used = bytes_used / (1024 * 1024)
        self.data_used_mb += mb_used
        self.save(update_fields=['data_used_mb', 'updated_at'])


class DeviceCapture(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='captures')
    image = models.TextField()  # Store base64 encoded image
    captured_at = models.DateTimeField(auto_now_add=True)
    data_size_bytes = models.IntegerField(default=0, help_text="Size of capture data in bytes")
    connection_type = models.CharField(
        max_length=20,
        choices=Device.CONNECTION_TYPE_CHOICES,
        default='unknown',
        help_text="Connection type used for this capture"
    )
    
    class Meta:
        ordering = ['-captured_at']
    
    def __str__(self):
        return f"Capture from {self.device.serial_number} at {self.captured_at}"


class Capture(models.Model):
    TRIGGER_TYPE_CHOICES = [
        ('automatic', 'Automatic (Timer)'),
        ('manual', 'Manual (User Request)'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    image_base64 = models.TextField()
    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPE_CHOICES,
        default='automatic',
        help_text="How this capture was triggered"
    )
    door_open = models.BooleanField(default=False, help_text="Door state when capture was taken")
    battery_voltage = models.FloatField(null=True, blank=True, help_text="Battery voltage at capture time")
    solar_charging = models.BooleanField(default=False, help_text="Solar charging status at capture time")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Capture from {self.device.serial_number} at {self.timestamp}"


class CaptureAnalysis(models.Model):
    """Store Firebase Vision API analysis results for captures"""
    capture = models.OneToOneField(Capture, on_delete=models.CASCADE, related_name='analysis')
    summary = models.CharField(max_length=500, help_text="AI-generated summary (e.g., 'Large Amazon package detected')")
    
    # Object detection results
    detected_objects = models.JSONField(default=list, help_text="List of detected objects with labels and confidence")
    package_detected = models.BooleanField(default=False)
    letter_detected = models.BooleanField(default=False)
    envelope_detected = models.BooleanField(default=False)
    
    # OCR results
    detected_text = models.TextField(blank=True, help_text="All detected text from OCR")
    return_addresses = models.JSONField(default=list, help_text="Extracted return addresses")
    
    # Logo/brand detection
    logos_detected = models.JSONField(default=list, help_text="Detected logos/brands (e.g., Amazon, FedEx)")
    
    # Size estimation
    estimated_size = models.CharField(max_length=20, blank=True, help_text="Estimated size: small, medium, large")
    
    # Bounding boxes for detected objects
    bounding_boxes = models.JSONField(default=list, help_text="Bounding box coordinates for detected objects")
    
    # Confidence and performance metrics
    confidence_score = models.FloatField(null=True, blank=True, help_text="Overall confidence score (0.0-1.0)")
    processing_time_ms = models.IntegerField(null=True, blank=True, help_text="Processing time in milliseconds")
    
    # Timestamps
    analysis_timestamp = models.DateTimeField(auto_now_add=True, help_text="When analysis was performed")
    
    # Email notification tracking
    email_sent = models.BooleanField(default=False, help_text="Email notification sent")
    email_sent_at = models.DateTimeField(null=True, blank=True, help_text="When email was sent")
    
    # Email acknowledgment tracking
    email_acknowledged = models.BooleanField(default=False, help_text="Customer replied to email")
    email_acknowledged_at = models.DateTimeField(null=True, blank=True, help_text="When customer replied")
    
    class Meta:
        verbose_name = "Capture Analysis"
        verbose_name_plural = "Capture Analyses"
        ordering = ['-analysis_timestamp']
    
    def __str__(self):
        return f"Analysis for {self.capture} - {self.summary}"


class PushSubscription(models.Model):
    """Web push notification subscriptions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'endpoint']
    
    def __str__(self):
        return f"Push subscription for {self.user.username}"
    
    def get_keys_dict(self):
        """Get keys as dictionary for pywebpush"""
        return {
            'p256dh': self.p256dh,
            'auth': self.auth
        }


class NotificationPreferences(models.Model):
    """User notification preferences for mail detection alerts"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Notification channels
    email_enabled = models.BooleanField(default=True, help_text='Enable email notifications')
    sms_enabled = models.BooleanField(default=False, help_text='Enable SMS notifications')
    push_enabled = models.BooleanField(default=True, help_text='Enable push notifications')
    
    # Notification timing
    immediate = models.BooleanField(default=True, help_text='Send immediate notifications (vs hourly summaries)')
    
    # Quiet hours
    quiet_hours_start = models.TimeField(default=time(22, 0), help_text='Start of quiet hours (no email/SMS)')
    quiet_hours_end = models.TimeField(default=time(7, 0), help_text='End of quiet hours')
    quiet_hours_enabled = models.BooleanField(default=True, help_text='Enable quiet hours')
    
    # Data optimization
    email_thumbnail_size = models.IntegerField(default=100, help_text='Email thumbnail size in KB')
    
    # SMS phone number
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text='Phone number for SMS (E.164 format: +1234567890)'
    )
    
    class Meta:
        verbose_name = 'Notification Preferences'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        now = timezone.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        # Handle quiet hours that span midnight
        if start > end:
            return now >= start or now <= end
        else:
            return start <= now <= end
