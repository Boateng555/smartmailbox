from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from .models import Device, DeviceCapture, SIM
from .serializers import HeartbeatSerializer, CaptureRequestSerializer, DeviceCaptureSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated requests from ESP32
def device_heartbeat(request):
    """
    Handle device heartbeat POST requests.
    Updates device last_seen timestamp.
    """
    serializer = HeartbeatSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.warning(f"Invalid heartbeat request: {serializer.errors}")
        return Response(
            {'error': 'Invalid request', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serial_number = serializer.validated_data['serial_number']
    connection_type = serializer.validated_data.get('connection_type', 'unknown')
    
    logger.debug(f"Heartbeat received from device: {serial_number} via {connection_type}")
    
    # Get or create device (auto-create if doesn't exist)
    device, created = Device.objects.get_or_create(
        serial_number=serial_number,
        defaults={'status': 'online', 'owner_id': 1}  # Default to first user (admin)
    )
    
    device.last_seen = timezone.now()
    device.status = 'online'
    device.connection_type = connection_type
    device.save()
    
    if created:
        logger.info(f"New device created via heartbeat: {serial_number}")
    
    return Response({
        'status': 'success',
        'message': 'Heartbeat received',
        'device_id': device.id,
        'device_created': created
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated requests from ESP32
def device_capture(request):
    """
    Handle device photo capture POST requests.
    Accepts serial_number, base64 encoded image, and optional motion_detected flag.
    Sets ir_sensor_status to 'motion_detected' if motion is detected.
    Auto-resets to 'idle' after 5 seconds.
    """
    serializer = CaptureRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serial_number = serializer.validated_data['serial_number']
    base64_image = serializer.validated_data['image']
    motion_detected = serializer.validated_data.get('motion_detected', False)
    connection_type = serializer.validated_data.get('connection_type', 'unknown')
    
    logger.info(f"Capture received from device: {serial_number} via {connection_type}, motion: {motion_detected}, size: {len(base64_image)} bytes")
    
    try:
        # Get or create device (auto-create if doesn't exist)
        device, created = Device.objects.get_or_create(
            serial_number=serial_number,
            defaults={'status': 'online', 'owner_id': 1}  # Default to first user (admin)
        )
        
        # Check if motion status should be reset (if more than 5 seconds have passed)
        device.reset_motion_status_if_expired()
        
        # If motion detected, update IR sensor status
        if motion_detected:
            device.ir_sensor_status = 'motion_detected'
            device.last_motion_time = timezone.now()
            
            # Send push notification to device owner
            try:
                from .models import PushSubscription
                from pywebpush import webpush, WebPushException
                import json
                from django.conf import settings
                
                subscriptions = PushSubscription.objects.filter(user=device.owner)
                for subscription in subscriptions:
                    try:
                        keys = subscription.get_keys_dict()
                        payload = json.dumps({
                            'title': 'Motion Detected!',
                            'body': f'Motion detected on device {serial_number}',
                            'icon': '/static/icons/icon-192x192.png',
                            'tag': f'motion-{serial_number}',
                            'data': {
                                'url': f'/device/{serial_number}/',
                                'device_serial': serial_number,
                                'capture_id': None  # Will be set after capture creation
                            },
                            'requireInteraction': True
                        })
                        
                        webpush(
                            subscription_info={
                                "endpoint": subscription.endpoint,
                                "keys": keys
                            },
                            data=payload,
                            vapid_private_key=getattr(settings, 'VAPID_PRIVATE_KEY', None),
                            vapid_claims={
                                "sub": f"mailto:{device.owner.email or 'admin@example.com'}"
                            }
                        )
                        logger.info(f"Push notification sent to {device.owner.username} for motion on {serial_number}")
                    except WebPushException as e:
                        logger.error(f"Failed to send push notification: {str(e)}")
                        # Remove invalid subscriptions
                        if e.response and e.response.status_code == 410:
                            subscription.delete()
                    except Exception as e:
                        logger.error(f"Error sending push notification: {str(e)}")
            except ImportError:
                logger.warning("pywebpush not installed, push notifications disabled")
            except Exception as e:
                logger.error(f"Error in push notification system: {str(e)}")
        
        # Calculate data size (base64 encoded string size)
        data_size_bytes = len(base64_image.encode('utf-8'))
        
        # Create capture record
        capture = DeviceCapture.objects.create(
            device=device,
            image=base64_image,
            data_size_bytes=data_size_bytes,
            connection_type=connection_type
        )
        
        # Track data usage if using cellular connection
        if connection_type == 'cellular':
            # Find SIM card for this device
            sim = device.sim_cards.filter(device=device).first()
            if sim:
                sim.add_data_usage(data_size_bytes)
                
                # Check if approaching limit and add warning
                warnings = []
                if sim.is_over_limit:
                    warnings.append('Data limit exceeded!')
                elif sim.is_near_limit:
                    warnings.append(f'Data usage at {sim.data_used_percent:.1f}% of limit')
        
        # Update device last_seen, status, and connection type
        device.last_seen = timezone.now()
        device.status = 'online'
        device.connection_type = connection_type
        device.save()
        
        # Send WebSocket message to device feed subscribers
        try:
            channel_layer = get_channel_layer()
            group_name = f'device_{serial_number}'
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'new_capture',
                    'capture_id': capture.id,
                    'image': base64_image,
                    'captured_at': capture.captured_at.isoformat(),
                    'motion_detected': motion_detected,
                    'device_status': device.status,
                    'ir_sensor_status': device.ir_sensor_status,
                }
            )
            logger.debug(f"WebSocket message sent for capture {capture.id} to device {serial_number}")
        except Exception as ws_error:
            # Log error but don't fail the request
            logger.error(f"WebSocket error for device {serial_number}: {str(ws_error)}")
        
        # Check for data usage warnings
        warnings = []
        if connection_type == 'cellular':
            sim = device.sim_cards.filter(device=device).first()
            if sim:
                if sim.is_over_limit:
                    warnings.append('Data limit exceeded!')
                elif sim.is_near_limit:
                    warnings.append(f'Data usage at {sim.data_used_percent:.1f}% of limit')
        
        response_data = {
            'status': 'success',
            'message': 'Capture stored successfully',
            'capture_id': capture.id,
            'device_id': device.id,
            'device_created': created,
            'ir_sensor_status': device.ir_sensor_status,
            'motion_detected': motion_detected,
            'connection_type': connection_type,
            'data_size_bytes': data_size_bytes,
        }
        
        if warnings:
            response_data['warnings'] = warnings
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Failed to store capture for device {serial_number}: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Failed to store capture', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

