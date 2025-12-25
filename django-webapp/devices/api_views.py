from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction
from .models import Device, Capture, CaptureAnalysis, PushSubscription
from .firebase_vision import get_vision_service
from .email_service import send_mail_notification
import logging
import json

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated requests from ESP32
def capture_upload(request):
    """
    Handle device photo capture POST requests.
    Accepts JSON: {"serial": "ESP-12345", "image": "base64string"}
    Saves to database and returns capture_id.
    """
    try:
        # Get data from request (accept both 'serial' and 'serial_number' for compatibility)
        serial_number = request.data.get('serial') or request.data.get('serial_number')
        image_base64 = request.data.get('image')
        
        # Validate required fields
        if not serial_number:
            return Response(
                {'error': 'Missing required field: serial'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not image_base64:
            return Response(
                {'error': 'Missing required field: image'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create device (auto-create if doesn't exist)
        device, created = Device.objects.get_or_create(
            serial_number=serial_number,
            defaults={'status': 'online', 'lifecycle_state': 'pre_activation'}
        )
        
        # Check if device can operate (subscription check)
        from .billing import check_usage_limits, record_notification
        
        if not device.can_operate() and device.owner:
            return Response(
                {'error': 'Device subscription not active. Please update payment method.'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        # Check usage limits before processing
        image_size_bytes = len(image_base64) * 3 / 4;  # Approximate base64 to bytes
        can_send, reason, usage_record = check_usage_limits(device, image_size_bytes)
        
        if not can_send:
            return Response(
                {
                    'error': 'Usage limit reached',
                    'reason': reason,
                    'notification_count': usage_record.notification_count if usage_record else 0,
                    'notification_limit': usage_record.notification_limit if usage_record else 0,
                    'data_used_mb': float(usage_record.data_used_mb) if usage_record else 0,
                    'data_limit_mb': usage_record.data_limit_mb if usage_record else 0
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Get additional fields from request
        trigger_type = request.data.get('trigger_type', 'automatic')  # 'automatic' or 'manual'
        door_open = request.data.get('door_open', False)
        battery_voltage = request.data.get('battery_voltage')
        solar_charging = request.data.get('solar_charging', False)
        connection_type = request.data.get('connection_type', 'unknown')
        
        # Update device last_seen and status
        device.last_seen = timezone.now()
        device.status = 'online'
        device.connection_type = connection_type
        device.save()
        
        # Create capture record
        capture = Capture.objects.create(
            device=device,
            image_base64=image_base64,
            trigger_type=trigger_type,
            door_open=door_open,
            battery_voltage=battery_voltage,
            solar_charging=solar_charging
        )
        
        logger.info(f"Capture saved: ID={capture.id}, Device={serial_number}, Trigger={trigger_type}, Door={door_open}")
        
        # Record notification usage
        if usage_record:
            record_notification(device, image_size_bytes)
        
        # Analyze image with Firebase Vision API (async in background)
        try:
            analysis_result = analyze_capture_async(capture)
            if analysis_result:
                logger.info(f"Analysis completed for capture {capture.id}: {analysis_result.get('summary', 'N/A')}")
        except Exception as analysis_error:
            logger.error(f"Failed to analyze capture {capture.id}: {str(analysis_error)}", exc_info=True)
        
        # Send WebSocket notification to device feed subscribers (allows multiple clients per device)
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f'device_{serial_number}'
                
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'new_capture',
                        'capture_id': capture.id,
                        'image': image_base64,
                        'captured_at': capture.timestamp.isoformat(),
                        'trigger_type': trigger_type,
                        'door_open': door_open,
                        'battery_voltage': battery_voltage,
                        'solar_charging': solar_charging,
                        'device_status': device.status,
                        'serial_number': serial_number,
                    }
                )
                logger.info(f"WebSocket message sent for capture {capture.id} to device {serial_number} (group: {group_name})")
            else:
                logger.warning("Channel layer not configured, skipping WebSocket notification")
        except Exception as ws_error:
            # Log error but don't fail the request
            logger.error(f"WebSocket error for device {serial_number}: {str(ws_error)}", exc_info=True)
        
        return Response({
            'status': 'saved',
            'capture_id': capture.id
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Failed to save capture: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to save capture', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def analyze_capture_async(capture: Capture):
    """
    Analyze a capture using Firebase Vision API and send notifications.
    This function is called asynchronously after capture is saved.
    """
    try:
        # Get Vision service
        vision_service = get_vision_service()
        
        # Analyze image using structured analysis
        analysis_data = vision_service.analyze_mail(capture.image_base64)
        
        # Generate summary from structured data
        summary_parts = []
        if analysis_data.get('size') and analysis_data['size'] != 'unknown':
            summary_parts.append(analysis_data['size'].title())
        if analysis_data.get('type') and analysis_data['type'] != 'unknown':
            summary_parts.append(analysis_data['type'])
        if analysis_data.get('carrier'):
            summary_parts.append(f"from {analysis_data['carrier']}")
        
        summary = " ".join(summary_parts).title() + " detected" if summary_parts else "Mail item detected"
        
        # Create CaptureAnalysis record
        with transaction.atomic():
            analysis = CaptureAnalysis.objects.create(
                capture=capture,
                summary=summary,
                detected_objects=[],  # Store raw analysis data if needed
                package_detected=(analysis_data.get('type') == 'package'),
                letter_detected=(analysis_data.get('type') == 'letter'),
                envelope_detected=(analysis_data.get('type') == 'envelope'),
                detected_text=analysis_data.get('text', ''),
                return_addresses=[],  # Can be extracted from text if needed
                logos_detected=[{'description': c, 'confidence': analysis_data.get('confidence', 0.0)} 
                               for c in analysis_data.get('carriers', [])],
                estimated_size=analysis_data.get('size', '').title(),
                bounding_boxes=[],
                confidence_score=analysis_data.get('confidence', 0.0),
                processing_time_ms=None  # Can be added if needed
            )
            
            logger.info(f"Analysis saved for capture {capture.id}: {analysis.summary}")
        
        # Get related captures (for 3 photos in email)
        # Find captures from same device within 10 seconds (same trigger event)
        related_captures = Capture.objects.filter(
            device=capture.device,
            timestamp__gte=capture.timestamp - timezone.timedelta(seconds=10),
            timestamp__lte=capture.timestamp + timezone.timedelta(seconds=10)
        ).exclude(id=capture.id).order_by('timestamp')[:2]  # Get 2 more for total of 3
        
        # Send notifications based on preferences
        from .notification_preferences import should_send_notification, get_notification_preferences
        from .sms_service import send_mail_detection_sms
        
        prefs = get_notification_preferences(capture.device.owner)
        
        # Send email notification with 3 photos (thumbnails)
        if should_send_notification(capture.device.owner, 'email'):
            try:
                email_sent = send_mail_notification(capture, analysis, related_captures)
                if email_sent:
                    analysis.email_sent = True
                    analysis.email_sent_at = timezone.now()
                    analysis.save(update_fields=['email_sent', 'email_sent_at'])
                    logger.info(f"Email notification sent for capture {capture.id} with {len(related_captures) + 1} photos")
            except Exception as email_error:
                logger.error(f"Failed to send email for capture {capture.id}: {str(email_error)}")
        
        # Send SMS notification
        if should_send_notification(capture.device.owner, 'sms'):
            try:
                # Get phone number from user profile
                phone_number = getattr(capture.device.owner, 'profile', None)
                if phone_number and hasattr(phone_number, 'phone_number') and phone_number.phone_number:
                    sms_sent = send_mail_detection_sms(phone_number.phone_number, capture, analysis)
                    if sms_sent:
                        logger.info(f"SMS notification sent for capture {capture.id}")
            except Exception as sms_error:
                logger.error(f"Failed to send SMS for capture {capture.id}: {str(sms_error)}")
        
        # Send push notification (not affected by quiet hours)
        if should_send_notification(capture.device.owner, 'push'):
            try:
                send_push_notification(capture, analysis)
            except Exception as push_error:
                logger.error(f"Failed to send push notification for capture {capture.id}: {str(push_error)}")
        
        # Update WebSocket with analysis results
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                group_name = f'device_{capture.device.serial_number}'
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'analysis_complete',
                        'capture_id': capture.id,
                        'analysis_summary': analysis.summary,
                        'analysis_id': analysis.id,
                    }
                )
        except Exception as ws_error:
            logger.error(f"WebSocket error for analysis: {str(ws_error)}")
        
        return analysis_data
        
    except Exception as e:
        logger.error(f"Error in analyze_capture_async: {str(e)}", exc_info=True)
        return None


def send_push_notification(capture: Capture, analysis: CaptureAnalysis):
    """
    Send push notification to web app users when mail is detected.
    """
    try:
        from pywebpush import webpush, WebPushException
        
        device = capture.device
        owner = device.owner
        
        # Get all push subscriptions for the device owner
        subscriptions = PushSubscription.objects.filter(user=owner)
        
        if not subscriptions.exists():
            logger.debug(f"No push subscriptions found for user {owner.username}")
            return
        
        # Prepare notification payload
        payload = {
            'title': '📬 Mail Detected in Your Smart Mailbox',
            'body': analysis.summary or 'New mail detected',
            'icon': '/static/icons/icon-192x192.png',
            'badge': '/static/icons/icon-192x192.png',
            'tag': f'mail-{capture.id}',
            'data': {
                'url': f'/device/{device.serial_number}/',
                'device_serial': device.serial_number,
                'capture_id': capture.id,
                'analysis_id': analysis.id,
                'summary': analysis.summary,
                'timestamp': capture.timestamp.isoformat(),
            },
            'requireInteraction': True,
            'actions': [
                {'action': 'view', 'title': 'View Details'},
                {'action': 'acknowledge', 'title': 'Acknowledge'}
            ],
            'vibrate': [200, 100, 200],
        }
        
        payload_json = json.dumps(payload)
        
        # Send to all subscriptions
        sent_count = 0
        for subscription in subscriptions:
            try:
                keys = subscription.get_keys_dict()
                
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": keys
                    },
                    data=payload_json,
                    vapid_private_key=getattr(settings, 'VAPID_PRIVATE_KEY', None),
                    vapid_claims={
                        "sub": f"mailto:{owner.email or 'admin@example.com'}"
                    }
                )
                sent_count += 1
                logger.debug(f"Push notification sent to subscription {subscription.id}")
                
            except WebPushException as e:
                logger.error(f"Failed to send push notification: {str(e)}")
                # Remove invalid subscriptions (410 = Gone)
                if e.response and e.response.status_code == 410:
                    logger.info(f"Removing invalid push subscription {subscription.id}")
                    subscription.delete()
            except Exception as e:
                logger.error(f"Error sending push notification: {str(e)}")
        
        if sent_count > 0:
            logger.info(f"Push notifications sent to {sent_count} subscription(s) for capture {capture.id}")
        
    except ImportError:
        logger.warning("pywebpush not installed. Push notifications disabled.")
    except Exception as e:
        logger.error(f"Failed to send push notifications: {str(e)}", exc_info=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_trigger(request):
    """
    Manual trigger endpoint for mobile app and web interface.
    Validates click limits and queues trigger request.
    """
    from .models import Device
    from django.utils import timezone
    from datetime import date
    
    try:
        device_serial = request.data.get('device_serial')
        if not device_serial:
            # Get user's first device if not specified
            device = Device.objects.filter(owner=request.user).first()
            if not device:
                return Response(
                    {'error': 'No device found. Please add a device first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            device = Device.objects.get(serial_number=device_serial, owner=request.user)
        
        # Check click limits based on subscription tier
        user = request.user
        is_premium = False
        click_limit = 3  # Default: free users get 3 clicks
        
        try:
            subscription = user.subscription
            if subscription and subscription.is_active:
                # Premium users get 10 clicks per day
                is_premium = subscription.plan.tier == 'premium' or subscription.plan.notification_limit == 0
                if is_premium:
                    click_limit = 10  # Premium users get 10 clicks per day
        except:
            pass
        
        # Check daily click limit (3 for free, 10 for premium)
        from django.db.models import Count
        today = timezone.now().date()
        # Check for manual triggers (captures with trigger_type='manual')
        today_clicks = Capture.objects.filter(
            device=device,
            timestamp__date=today,
            trigger_type='manual'
        ).count()
        
        if today_clicks >= click_limit:
            # Calculate reset time (midnight)
            tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
            return Response(
                {
                    'status': 'error',
                    'error': 'click_limit_exceeded',
                    'message': f'You have reached your daily limit of {click_limit} manual clicks',
                    'clicks_used': today_clicks,
                    'clicks_limit': click_limit,
                    'reset_at': tomorrow.isoformat()
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Queue manual trigger (device will check on next wake cycle)
        # For now, we'll just return success - device will capture on next 2-hour cycle
        # In future, can add cellular wake functionality
        
        logger.info(f"Manual trigger requested for device {device.serial_number} by user {user.username}")
        
        return Response(
            {
                'status': 'queued',
                'message': 'Device will capture photo on next wake cycle (within 2 hours)',
                'device_serial': device.serial_number
            },
            status=status.HTTP_202_ACCEPTED
        )
    
    except Device.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in manual_trigger: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def click_status(request):
    """
    Get click limit status for current user.
    """
    from .models import Device
    from django.utils import timezone
    from datetime import date
    
    user = request.user
    device_serial = request.GET.get('device_serial')
    
    try:
        if device_serial:
            device = Device.objects.get(serial_number=device_serial, owner=user)
        else:
            device = Device.objects.filter(owner=user).first()
    except Device.DoesNotExist:
        device = None
    
    # Check subscription first to determine limit
    is_premium = False
    click_limit = 3  # Default: free users get 3 clicks
    
    try:
        subscription = user.subscription
        if subscription and subscription.is_active:
            is_premium = subscription.plan.tier == 'premium' or subscription.plan.notification_limit == 0
            if is_premium:
                click_limit = 10  # Premium users get 10 clicks per day
    except:
        pass
    
    if not device:
        return Response({
            'has_device': False,
            'clicks_used_today': 0,
            'clicks_limit': click_limit,
            'user_tier': 'premium' if is_premium else 'free'
        })
    
    # Get today's clicks (manual triggers only)
    today = timezone.now().date()
    today_clicks = Capture.objects.filter(
        device=device,
        timestamp__date=today,
        trigger_type='manual'
    ).count()
    
    # Calculate reset time
    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
    
    return Response({
        'has_device': True,
        'device_serial': device.serial_number,
        'clicks_used_today': today_clicks,
        'clicks_limit': click_limit,
        'clicks_remaining': max(0, click_limit - today_clicks),
        'user_tier': 'premium' if is_premium else 'free',
        'can_click': today_clicks < click_limit,
        'reset_at': tomorrow.isoformat()
    })


@api_view(['POST'])
@permission_classes([AllowAny])  # Stripe webhooks don't use Django auth
def stripe_webhook(request):
    """
    Handle Stripe webhook events for subscription management.
    """
    from .stripe_service import handle_stripe_webhook, get_stripe_client
    
    stripe = get_stripe_client()
    if not stripe:
        return Response(
            {'error': 'Stripe not configured'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    if not webhook_secret:
        logger.warning("STRIPE_WEBHOOK_SECRET not configured")
        return Response(
            {'error': 'Webhook secret not configured'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return Response(
            {'error': 'Invalid payload'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Invalid signature: {str(e)}")
        return Response(
            {'error': 'Invalid signature'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle the event
    try:
        handle_stripe_webhook(event)
        logger.info(f"Stripe webhook processed: {event['type']}")
        return Response({'status': 'success'})
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

