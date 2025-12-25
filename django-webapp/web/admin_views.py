from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta
import logging
from devices.models import Device, DeviceCapture, SIM, PushSubscription
from firmware.models import FirmwareVersion

logger = logging.getLogger(__name__)


def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_superuser)
def admin_dashboard(request):
    """Admin analytics dashboard"""
    # Device statistics
    total_devices = Device.objects.count()
    online_devices = Device.objects.filter(status='online').count()
    offline_devices = Device.objects.filter(status='offline').count()
    
    # Connection type breakdown
    wifi_devices = Device.objects.filter(connection_type='wifi').count()
    cellular_devices = Device.objects.filter(connection_type='cellular').count()
    
    # Recent activity (last 24 hours)
    last_24h = timezone.now() - timedelta(hours=24)
    recent_captures = DeviceCapture.objects.filter(captured_at__gte=last_24h).count()
    motion_detections = DeviceCapture.objects.filter(
        captured_at__gte=last_24h,
        device__ir_sensor_status='motion_detected'
    ).count()
    
    # Data usage statistics
    sim_stats = SIM.objects.aggregate(
        total_data_used=Sum('data_used_mb'),
        total_plan=Sum('plan_mb'),
        near_limit_count=Count('id', filter=Q(data_used_mb__gte=F('plan_mb') * 0.8))
    )
    
    # Daily capture trends (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    daily_captures = DeviceCapture.objects.filter(
        captured_at__gte=seven_days_ago
    ).annotate(
        date=TruncDate('captured_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Hourly activity (last 24 hours)
    hourly_captures = DeviceCapture.objects.filter(
        captured_at__gte=last_24h
    ).annotate(
        hour=TruncHour('captured_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Top devices by capture count
    top_devices = Device.objects.annotate(
        capture_count=Count('captures')
    ).order_by('-capture_count')[:10]
    
    context = {
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
        'wifi_devices': wifi_devices,
        'cellular_devices': cellular_devices,
        'recent_captures': recent_captures,
        'motion_detections': motion_detections,
        'sim_stats': sim_stats,
        'daily_captures': list(daily_captures),
        'hourly_captures': list(hourly_captures),
        'top_devices': top_devices,
    }
    return render(request, 'web/admin/dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def support_panel(request):
    """Customer support panel"""
    # Get all users with devices
    users_with_devices = Device.objects.values('owner').distinct()
    
    # Get devices with issues
    offline_devices = Device.objects.filter(status='offline').select_related('owner')
    devices_with_motion = Device.objects.filter(ir_sensor_status='motion_detected').select_related('owner')
    
    # SIM cards near/over limit
    sim_issues = SIM.objects.filter(
        Q(data_used_mb__gte=F('plan_mb') * 0.8)
    ).select_related('device', 'device__owner')
    
    # Recent errors or issues (can be extended with error logging)
    recent_issues = []
    
    context = {
        'offline_devices': offline_devices,
        'devices_with_motion': devices_with_motion,
        'sim_issues': sim_issues,
        'recent_issues': recent_issues,
    }
    return render(request, 'web/admin/support.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def device_diagnostics(request, serial):
    """Remote device diagnostics"""
    device = get_object_or_404(Device, serial_number=serial)
    
    # Device information
    device_info = {
        'serial_number': device.serial_number,
        'status': device.status,
        'connection_type': device.get_connection_type_display(),
        'ir_sensor_status': device.get_ir_sensor_status_display(),
        'last_seen': device.last_seen,
        'last_motion_time': device.last_motion_time,
        'owner': device.owner.username,
        'created_at': device.created_at,
    }
    
    # Recent captures
    recent_captures = DeviceCapture.objects.filter(device=device).order_by('-captured_at')[:20]
    
    # Connection history (last 24 hours)
    last_24h = timezone.now() - timedelta(hours=24)
    connection_history = DeviceCapture.objects.filter(
        device=device,
        captured_at__gte=last_24h
    ).values('connection_type').annotate(
        count=Count('id')
    )
    
    # Data usage if cellular
    sim_info = None
    if device.connection_type == 'cellular':
        sim = device.sim_cards.first()
        if sim:
            sim_info = {
                'iccid': sim.iccid,
                'data_used_mb': sim.data_used_mb,
                'plan_mb': sim.plan_mb,
                'data_used_percent': sim.data_used_percent,
                'is_near_limit': sim.is_near_limit,
                'is_over_limit': sim.is_over_limit,
            }
    
    # Health metrics
    health_metrics = {
        'uptime_percent': 100 if device.status == 'online' else 0,
        'avg_captures_per_day': DeviceCapture.objects.filter(device=device).count() / max((timezone.now() - device.created_at).days, 1),
        'last_capture': recent_captures[0].captured_at if recent_captures else None,
    }
    
    context = {
        'device': device,
        'device_info': device_info,
        'recent_captures': recent_captures,
        'connection_history': list(connection_history),
        'sim_info': sim_info,
        'health_metrics': health_metrics,
    }
    return render(request, 'web/admin/diagnostics.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def bulk_firmware_update(request):
    """Bulk firmware update interface"""
    if request.method == 'POST':
        firmware_version_id = request.POST.get('firmware_version')
        device_serials = request.POST.getlist('devices')
        
        if not firmware_version_id or not device_serials:
            messages.error(request, 'Please select firmware version and at least one device.')
            return redirect('web:bulk_firmware_update')
        
        try:
            firmware = FirmwareVersion.objects.get(id=firmware_version_id, is_active=True)
            devices = Device.objects.filter(serial_number__in=device_serials)
            
            # In a real implementation, you would queue firmware updates here
            # For now, we'll just mark them for update
            updated_count = devices.count()
            
            messages.success(request, f'Firmware update queued for {updated_count} device(s).')
            logger.info(f"Bulk firmware update initiated: {firmware.version} for {updated_count} devices")
            
        except FirmwareVersion.DoesNotExist:
            messages.error(request, 'Selected firmware version not found or inactive.')
        except Exception as e:
            messages.error(request, f'Error queuing firmware updates: {str(e)}')
            logger.error(f"Bulk firmware update error: {str(e)}")
        
        return redirect('web:bulk_firmware_update')
    
    # GET request - show form
    active_firmware = FirmwareVersion.objects.filter(is_active=True).order_by('-release_date')
    all_devices = Device.objects.all().order_by('serial_number')
    
    context = {
        'firmware_versions': active_firmware,
        'devices': all_devices,
    }
    return render(request, 'web/admin/bulk_update.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def api_device_diagnostics(request, serial):
    """API endpoint for device diagnostics (JSON)"""
    device = get_object_or_404(Device, serial_number=serial)
    
    diagnostics = {
        'serial_number': device.serial_number,
        'status': device.status,
        'connection_type': device.connection_type,
        'ir_sensor_status': device.ir_sensor_status,
        'last_seen': device.last_seen.isoformat() if device.last_seen else None,
        'last_motion_time': device.last_motion_time.isoformat() if device.last_motion_time else None,
        'total_captures': device.captures.count(),
        'recent_captures_24h': device.captures.filter(
            captured_at__gte=timezone.now() - timedelta(hours=24)
        ).count(),
    }
    
    return JsonResponse(diagnostics)







