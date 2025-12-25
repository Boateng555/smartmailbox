from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, FileResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.conf import settings
import logging
from devices.models import Device, DeviceCapture, Capture, CaptureAnalysis, SIM, PushSubscription
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """
    Customer dashboard showing recent mail with AI tags and device overview.
    """
    logger.info(f"Dashboard accessed by user: {request.user.username}")
    devices = Device.objects.filter(owner=request.user).order_by('-last_seen')
    
    # Get recent mail (captures with analysis) from all user's devices
    recent_mail = Capture.objects.filter(
        device__owner=request.user
    ).select_related('device', 'analysis').prefetch_related('analysis').order_by('-timestamp')[:20]
    
    # Get statistics
    total_devices = devices.count()
    online_devices = devices.filter(status='online').count()
    recent_mail_count = recent_mail.count()
    
    context = {
        'devices': devices,
        'recent_mail': recent_mail,
        'total_devices': total_devices,
        'online_devices': online_devices,
        'recent_mail_count': recent_mail_count,
        'user': request.user,
    }
    return render(request, 'web/dashboard.html', context)


@login_required
def device_detail(request, serial):
    """
    Device detail view showing recent captures, battery status, and device information.
    """
    logger.info(f"Device detail accessed: {serial} by user: {request.user.username}")
    device = get_object_or_404(Device, serial_number=serial, owner=request.user)
    
    # Get recent captures with analysis
    recent_captures = Capture.objects.filter(device=device).select_related('analysis').order_by('-timestamp')[:20]
    
    # Get latest battery status from most recent capture
    latest_capture = recent_captures.first()
    battery_voltage = latest_capture.battery_voltage if latest_capture else None
    solar_charging = latest_capture.solar_charging if latest_capture else False
    
    context = {
        'device': device,
        'recent_captures': recent_captures,
        'battery_voltage': battery_voltage,
        'solar_charging': solar_charging,
        'user': request.user,
        'device_serial': serial,
    }
    return render(request, 'web/device_detail.html', context)


@login_required
def download_capture(request, capture_id):
    """
    Download a capture image as a JPEG file to the user's device.
    """
    from django.http import HttpResponse
    import base64
    from datetime import datetime
    
    capture = get_object_or_404(Capture, id=capture_id, device__owner=request.user)
    
    try:
        # Decode base64 image
        image_data = base64.b64decode(capture.image_base64)
        
        # Create filename with timestamp
        timestamp = capture.timestamp.strftime('%Y%m%d_%H%M%S')
        filename = f"capture_{capture.device.serial_number}_{timestamp}.jpg"
        
        # Create HTTP response with image data
        response = HttpResponse(image_data, content_type='image/jpeg')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(image_data)
        
        return response
    except Exception as e:
        logger.error(f"Error downloading capture {capture_id}: {str(e)}")
        return HttpResponse("Error downloading image", status=500)


@login_required
def photo_gallery(request, serial=None):
    """
    Photo gallery view with AI tags and filtering.
    """
    logger.info(f"Photo gallery accessed by user: {request.user.username}")
    
    if serial:
        device = get_object_or_404(Device, serial_number=serial, owner=request.user)
        captures = Capture.objects.filter(device=device).select_related('analysis').order_by('-timestamp')
    else:
        # All devices
        captures = Capture.objects.filter(device__owner=request.user).select_related('device', 'analysis').order_by('-timestamp')
    
    # Filtering
    filter_type = request.GET.get('type', 'all')
    if filter_type == 'package':
        captures = captures.filter(analysis__package_detected=True)
    elif filter_type == 'letter':
        captures = captures.filter(analysis__letter_detected=True)
    elif filter_type == 'envelope':
        captures = captures.filter(analysis__envelope_detected=True)
    
    # Pagination
    paginator = Paginator(captures, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'captures': page_obj,
        'device': device if serial else None,
        'filter_type': filter_type,
        'user': request.user,
    }
    return render(request, 'web/photo_gallery.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def settings(request):
    """
    Settings page for notification preferences and account settings.
    """
    logger.info(f"Settings accessed by user: {request.user.username}")
    
    if request.method == 'POST':
        # Handle notification preferences
        try:
            from devices.models import NotificationPreferences
            prefs, created = NotificationPreferences.objects.get_or_create(user=request.user)
            prefs.email_enabled = request.POST.get('email_notifications', 'off') == 'on'
            prefs.sms_enabled = request.POST.get('sms_notifications', 'off') == 'on'
            prefs.push_enabled = request.POST.get('push_notifications', 'off') == 'on'
            prefs.save()
        except Exception as e:
            logger.warning(f"Could not save notification preferences: {e}")
            # Fallback to session
            request.session['email_notifications'] = request.POST.get('email_notifications', 'off') == 'on'
            request.session['push_notifications'] = request.POST.get('push_notifications', 'off') == 'on'
        
        messages.success(request, 'Settings saved successfully!')
        return redirect('web:settings')
    
    # Get subscription information
    try:
        from devices.subscription_models import CustomerSubscription
        subscription = request.user.subscription
    except:
        subscription = None
    
    # Get notification preferences
    try:
        from devices.models import NotificationPreferences
        prefs = NotificationPreferences.objects.get(user=request.user)
        email_notifications = prefs.email_enabled
        push_notifications = prefs.push_enabled
        sms_notifications = prefs.sms_enabled
    except:
        email_notifications = request.session.get('email_notifications', True)
        push_notifications = request.session.get('push_notifications', True)
        sms_notifications = False
    
    # Get push subscription status
    push_subscriptions = PushSubscription.objects.filter(user=request.user)
    has_push_subscription = push_subscriptions.exists()
    
    # Get user's devices
    from devices.models import Device
    devices = Device.objects.filter(owner=request.user)
    
    context = {
        'user': request.user,
        'subscription': subscription,
        'email_notifications': email_notifications,
        'sms_notifications': sms_notifications,
        'push_notifications': push_notifications,
        'has_push_subscription': has_push_subscription,
        'devices': devices,
        'VAPID_PUBLIC_KEY': getattr(settings, 'VAPID_PUBLIC_KEY', ''),
    }
    return render(request, 'web/settings.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def claim_device(request):
    """
    Device claiming page with setup wizard that guides users through:
    1. Turn on device
    2. Connect to setup WiFi
    3. Enter home WiFi credentials
    4. Return to app and claim device
    """
    logger.info(f"Claim device page accessed by user: {request.user.username}")
    if request.method == 'POST':
        serial_number = request.POST.get('serial_number', '').strip().upper()
        
        if not serial_number:
            messages.error(request, 'Please enter a serial number.')
            return render(request, 'web/claim_device.html', {
                'user': request.user,
                'current_step': 4
            })
        
        # Validate serial number format (ESP-XXXXXX)
        if not serial_number.startswith('ESP-') or len(serial_number) != 10:
            messages.error(request, 'Invalid serial number format. Expected format: ESP-XXXXXX')
            return render(request, 'web/claim_device.html', {
                'user': request.user,
                'current_step': 4
            })
        
        # Check if device exists
        try:
            device = Device.objects.get(serial_number=serial_number)
            
            # Check if device is already claimed
            if device.owner != request.user:
                if device.owner_id == 1:  # Default admin user (unclaimed)
                    # Claim the device
                    device.owner = request.user
                    device.save()
                    logger.info(f"Device {serial_number} claimed by user: {request.user.username}")
                    messages.success(request, f'Device {serial_number} has been claimed successfully!')
                    return redirect('web:dashboard')
                else:
                    logger.warning(f"Device {serial_number} already claimed by another user")
                    messages.error(request, 'This device is already claimed by another user.')
            else:
                messages.info(request, 'You already own this device.')
                return redirect('web:device_detail', serial=serial_number)
                
        except Device.DoesNotExist:
            # Device doesn't exist yet - create it and claim it
            device = Device.objects.create(
                serial_number=serial_number,
                owner=request.user,
                status='offline'
            )
            logger.info(f"New device {serial_number} created and claimed by user: {request.user.username}")
            messages.success(request, f'Device {serial_number} has been claimed successfully!')
            return redirect('web:dashboard')
    
    # Get current step from query parameter (for step navigation)
    current_step = int(request.GET.get('step', 1))
    
    context = {
        'user': request.user,
        'current_step': current_step,
        'setup_wifi_ssid': 'SmartCamera-SETUP',
        'setup_wifi_url': 'http://192.168.4.1/config',
    }
    return render(request, 'web/claim_device.html', context)


def manifest(request):
    """
    Serve the PWA manifest.json file.
    """
    manifest_content = render_to_string('manifest.json', request=request)
    response = HttpResponse(manifest_content, content_type='application/manifest+json')
    return response


def service_worker(request):
    """
    Serve the service worker JavaScript file.
    """
    sw_content = render_to_string('service-worker.js', request=request)
    response = HttpResponse(sw_content, content_type='application/javascript')
    # Service workers must be served with no-cache headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
@require_http_methods(["POST"])
def subscribe_push(request):
    """
    Register a push notification subscription for the current user.
    """
    try:
        import json
        from devices.models import PushSubscription
        
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        keys = json.dumps(data.get('keys', {}))
        
        if not endpoint:
            return JsonResponse({'error': 'Missing endpoint'}, status=400)
        
        subscription, created = PushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={'keys': keys}
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Subscription registered' if created else 'Subscription updated'
        })
    except Exception as e:
        logger.error(f"Error registering push subscription: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_superuser)
def debug_page(request):
    """
    Debug page showing system status, devices, and recent activity.
    """
    logger.info(f"Debug page accessed by user: {request.user.username}")
    
    # Get all devices with statistics
    all_devices = Device.objects.all().order_by('-last_seen')
    
    # Device statistics
    device_stats = {
        'total': all_devices.count(),
        'online': all_devices.filter(status='online').count(),
        'offline': all_devices.filter(status='offline').count(),
        'wifi': all_devices.filter(connection_type='wifi').count(),
        'cellular': all_devices.filter(connection_type='cellular').count(),
    }
    
    # Recent captures (last 50)
    recent_captures = DeviceCapture.objects.all().order_by('-captured_at')[:50]
    
    # SIM card statistics
    sim_cards = SIM.objects.all()
    sim_stats = {
        'total': sim_cards.count(),
        'near_limit': sum(1 for sim in sim_cards if sim.is_near_limit),
        'over_limit': sum(1 for sim in sim_cards if sim.is_over_limit),
        'total_data_used': sum(sim.data_used_mb for sim in sim_cards),
    }
    
    # Connection type breakdown
    connection_breakdown = all_devices.values('connection_type').annotate(
        count=Count('id')
    )
    
    context = {
        'devices': all_devices,
        'device_stats': device_stats,
        'recent_captures': recent_captures,
        'sim_cards': sim_cards,
        'sim_stats': sim_stats,
        'connection_breakdown': connection_breakdown,
        'user': request.user,
    }
    return render(request, 'web/debug.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def test_websocket(request, serial):
    """
    Test WebSocket connection for a specific device.
    """
    logger.info(f"WebSocket test requested for device: {serial} by user: {request.user.username}")
    
    try:
        device = Device.objects.get(serial_number=serial)
        group_name = f'device_{serial}'
        
        # Try to send a test message via WebSocket
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'test_message',
                    'message': 'Test message from debug page',
                    'timestamp': timezone.now().isoformat(),
                }
            )
            return JsonResponse({
                'status': 'success',
                'message': f'Test message sent to device {serial}',
                'group_name': group_name
            })
        except Exception as e:
            logger.error(f"WebSocket test failed for {serial}: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to send test message: {str(e)}'
            }, status=500)
    except Device.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Device {serial} not found'
            }, status=404)


class MobileLoginView(LoginView):
    """Custom login view for mobile-friendly interface"""
    template_name = 'web/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('web:dashboard')


@require_http_methods(["GET", "POST"])
def mobile_logout(request):
    """Logout view for mobile"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('web:login')
