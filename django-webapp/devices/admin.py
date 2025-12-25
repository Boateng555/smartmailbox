from django.contrib import admin
from .models import Device, DeviceCapture, SIM, PushSubscription, Capture, CaptureAnalysis
from .subscription_models import SubscriptionPlan, CustomerSubscription, DataUsage, PaymentHistory


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'status', 'connection_type', 'power_state', 'owner', 'last_seen', 'created_at')
    list_filter = ('status', 'connection_type', 'power_state', 'lifecycle_state', 'created_at')
    search_fields = ('serial_number', 'owner__username')
    readonly_fields = ('created_at',)


@admin.register(SIM)
class SIMAdmin(admin.ModelAdmin):
    list_display = ('iccid', 'device', 'data_used_mb', 'plan_mb', 'data_used_percent', 'is_near_limit', 'is_over_limit', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('iccid', 'device__serial_number')
    readonly_fields = ('data_used_percent', 'is_near_limit', 'is_over_limit', 'created_at', 'updated_at')


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'endpoint')
    readonly_fields = ('created_at',)


@admin.register(DeviceCapture)
class DeviceCaptureAdmin(admin.ModelAdmin):
    list_display = ('device', 'captured_at', 'connection_type', 'data_size_bytes')
    list_filter = ('captured_at', 'connection_type')
    search_fields = ('device__serial_number',)
    readonly_fields = ('captured_at',)


@admin.register(Capture)
class CaptureAdmin(admin.ModelAdmin):
    list_display = ('device', 'timestamp', 'trigger_type', 'door_open', 'battery_voltage', 'solar_charging')
    list_filter = ('timestamp', 'trigger_type', 'door_open', 'solar_charging')
    search_fields = ('device__serial_number',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(CaptureAnalysis)
class CaptureAnalysisAdmin(admin.ModelAdmin):
    list_display = ('capture', 'summary', 'package_detected', 'letter_detected', 'envelope_detected', 
                   'estimated_size', 'email_sent', 'email_acknowledged', 'analysis_timestamp')
    list_filter = ('package_detected', 'letter_detected', 'envelope_detected', 'email_sent', 
                  'email_acknowledged', 'analysis_timestamp')
    search_fields = ('summary', 'capture__device__serial_number', 'detected_text')
    readonly_fields = ('analysis_timestamp', 'processing_time_ms', 'email_sent_at', 
                      'email_acknowledged_at')
    date_hierarchy = 'analysis_timestamp'
    
    fieldsets = (
        ('Capture Info', {
            'fields': ('capture', 'summary', 'analysis_timestamp', 'processing_time_ms', 'confidence_score')
        }),
        ('Detection Results', {
            'fields': ('package_detected', 'letter_detected', 'envelope_detected', 'estimated_size', 
                      'detected_objects', 'bounding_boxes')
        }),
        ('OCR Results', {
            'fields': ('detected_text', 'return_addresses', 'logos_detected')
        }),
        ('Notifications', {
            'fields': ('email_sent', 'email_sent_at', 'email_acknowledged', 'email_acknowledged_at')
        }),
    )


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'price_monthly', 'notification_limit', 'data_limit_mb', 'is_active')
    list_filter = ('tier', 'is_active')
    search_fields = ('name', 'tier')
    readonly_fields = ('created_at',)


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'current_period_start', 'current_period_end', 'is_active', 'days_until_renewal')
    list_filter = ('status', 'plan', 'auto_renew', 'created_at')
    search_fields = ('user__username', 'user__email', 'stripe_subscription_id', 'stripe_customer_id')
    readonly_fields = ('created_at', 'updated_at', 'days_until_renewal', 'is_in_trial', 'is_in_grace_period')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Customer', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Billing', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id', 'stripe_payment_method_id', 'auto_renew')
        }),
        ('Dates', {
            'fields': ('trial_start', 'trial_end', 'current_period_start', 'current_period_end', 'cancelled_at', 'grace_period_end')
        }),
        ('Status', {
            'fields': ('is_active', 'is_in_trial', 'is_in_grace_period', 'days_until_renewal')
        }),
    )


@admin.register(DataUsage)
class DataUsageAdmin(admin.ModelAdmin):
    list_display = ('device', 'subscription', 'year', 'month', 'notification_count', 'notification_limit', 
                   'data_used_mb', 'data_limit_mb', 'is_over_limit', 'overage_charge')
    list_filter = ('year', 'month', 'subscription__plan')
    search_fields = ('device__serial_number', 'subscription__user__username')
    readonly_fields = ('notification_usage_percent', 'data_usage_percent', 'is_near_limit', 'is_over_limit', 
                      'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'amount', 'status', 'paid_at', 'created_at', 'stripe_invoice_id')
    list_filter = ('status', 'created_at')
    search_fields = ('subscription__user__username', 'stripe_payment_intent_id', 'stripe_invoice_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
