"""
Customer portal views for dashboard, gallery, settings, and billing.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from .models import Device, Capture, CaptureAnalysis
from .subscription_models import CustomerSubscription, DataUsage, PaymentHistory, SubscriptionPlan
from .notification_preferences import get_notification_preferences
import json


@login_required
def dashboard(request):
    """Customer dashboard with device status and recent activity"""
    user = request.user
    
    # Get user's devices
    devices = Device.objects.filter(owner=user)
    
    # Get subscription
    try:
        subscription = user.subscription
        is_active = subscription.is_active
    except CustomerSubscription.DoesNotExist:
        subscription = None
        is_active = False
    
    # Get current month usage
    now = timezone.now()
    usage_records = DataUsage.objects.filter(
        subscription__user=user,
        year=now.year,
        month=now.month
    )
    
    total_notifications = usage_records.aggregate(Sum('notification_count'))['notification_count__sum'] or 0
    total_data_mb = usage_records.aggregate(Sum('data_used_mb'))['data_used_mb__sum'] or 0
    
    # Get recent captures
    recent_captures = Capture.objects.filter(
        device__owner=user
    ).select_related('device', 'analysis').order_by('-timestamp')[:10]
    
    # Get device status summary
    online_devices = devices.filter(status='online').count()
    offline_devices = devices.filter(status='offline').count()
    
    context = {
        'devices': devices,
        'subscription': subscription,
        'is_active': is_active,
        'total_notifications': total_notifications,
        'total_data_mb': float(total_data_mb),
        'recent_captures': recent_captures,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
    }
    
    return render(request, 'devices/customer/dashboard.html', context)


@login_required
def gallery(request):
    """Photo gallery with AI categorization"""
    user = request.user
    
    # Get filter parameters
    device_serial = request.GET.get('device')
    mail_type = request.GET.get('type')  # package, letter, envelope
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Base queryset
    captures = Capture.objects.filter(device__owner=user).select_related('device', 'analysis')
    
    # Apply filters
    if device_serial:
        captures = captures.filter(device__serial_number=device_serial)
    
    if mail_type:
        if mail_type == 'package':
            captures = captures.filter(analysis__package_detected=True)
        elif mail_type == 'letter':
            captures = captures.filter(analysis__letter_detected=True)
        elif mail_type == 'envelope':
            captures = captures.filter(analysis__envelope_detected=True)
    
    if date_from:
        captures = captures.filter(timestamp__gte=date_from)
    
    if date_to:
        captures = captures.filter(timestamp__lte=date_to)
    
    captures = captures.order_by('-timestamp')[:100]  # Limit to 100 most recent
    
    # Get device list for filter
    devices = Device.objects.filter(owner=user)
    
    context = {
        'captures': captures,
        'devices': devices,
        'filters': {
            'device': device_serial,
            'type': mail_type,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'devices/customer/gallery.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def settings(request):
    """Customer settings page"""
    user = request.user
    
    if request.method == 'POST':
        # Handle notification preferences update
        try:
            from .models import NotificationPreferences as NotificationPrefsModel
            prefs_model, created = NotificationPrefsModel.objects.get_or_create(user=user)
            prefs_model.email_enabled = request.POST.get('email_notifications', 'off') == 'on'
            prefs_model.sms_enabled = request.POST.get('sms_notifications', 'off') == 'on'
            prefs_model.push_enabled = request.POST.get('push_notifications', 'off') == 'on'
            prefs_model.save()
        except Exception as e:
            # If model doesn't exist, just log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not save notification preferences: {e}")
        
        messages.success(request, 'Settings saved successfully!')
        return redirect('devices:settings')
    
    # Get subscription
    try:
        subscription = user.subscription
    except CustomerSubscription.DoesNotExist:
        subscription = None
    
    # Get notification preferences
    prefs = get_notification_preferences(user)
    
    # Get NotificationPreferences model if it exists
    try:
        from .models import NotificationPreferences as NotificationPrefsModel
        prefs_model = NotificationPrefsModel.objects.get(user=user)
        preferences_dict = {
            'email_enabled': prefs_model.email_enabled,
            'sms_enabled': prefs_model.sms_enabled,
            'push_enabled': prefs_model.push_enabled,
        }
    except:
        # Fallback to preferences object
        preferences_dict = prefs.preferences
    
    # Get devices
    devices = Device.objects.filter(owner=user)
    
    context = {
        'subscription': subscription,
        'preferences': preferences_dict,
        'devices': devices,
        'user': user,
    }
    
    return render(request, 'devices/customer/settings.html', context)


@login_required
def billing(request):
    """Billing and subscription management"""
    user = request.user
    
    # Get subscription
    try:
        subscription = user.subscription
    except CustomerSubscription.DoesNotExist:
        subscription = None
    
    # Get all available plans for upgrade/downgrade
    available_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
    
    # Get payment history
    payments = []
    if subscription:
        payments = PaymentHistory.objects.filter(subscription=subscription).order_by('-created_at')[:20]
    
    # Get current usage
    now = timezone.now()
    usage_records = []
    if subscription:
        usage_records = DataUsage.objects.filter(
            subscription=subscription,
            year=now.year,
            month=now.month
        )
    
    context = {
        'subscription': subscription,
        'available_plans': available_plans,
        'payments': payments,
        'usage_records': usage_records,
        'user': user,
    }
    
    return render(request, 'devices/customer/billing.html', context)
