import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from devices.models import Device

logger = logging.getLogger(__name__)


class DeviceFeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.serial_number = self.scope['url_route']['kwargs']['serial']
        self.room_group_name = f'device_{self.serial_number}'
        
        # Check if user is authenticated
        user = self.scope.get('user')
        if isinstance(user, AnonymousUser):
            logger.warning(f"WebSocket connection rejected: unauthenticated user for device {self.serial_number}")
            await self.close()
            return
        
        # Verify user owns the device
        device = await self.get_device(self.serial_number, user.id)
        if not device:
            logger.warning(f"WebSocket connection rejected: user {user.username} does not own device {self.serial_number}")
            await self.close()
            return
        
        # Join room group (allows multiple clients per device)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected: user {user.username} to device {self.serial_number} (channel: {self.channel_name})")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': f'Connected to device feed: {self.serial_number}',
            'serial_number': self.serial_number
        }))
    
    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: device {self.serial_number}, code: {close_code}, channel: {self.channel_name}")
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        
        # Echo message back (for testing)
        await self.send(text_data=json.dumps({
            'type': 'echo',
            'message': message
        }))
    
    # Receive message from room group
    async def new_capture(self, event):
        # Send message to WebSocket (broadcasts to all connected clients for this device)
        logger.debug(f"Sending new_capture event to WebSocket for device {self.serial_number} (channel: {self.channel_name})")
        try:
            await self.send(text_data=json.dumps({
                'type': 'new_capture',
                'capture_id': event.get('capture_id'),
                'image': event.get('image', ''),
                'captured_at': event.get('captured_at', ''),
                'trigger_type': event.get('trigger_type', 'automatic'),
                'device_status': event.get('device_status', 'online'),
                'serial_number': self.serial_number
            }))
        except Exception as e:
            logger.error(f"Error sending new_capture to WebSocket for device {self.serial_number}: {str(e)}")
    
    async def test_message(self, event):
        """Handle test messages from debug page"""
        logger.info(f"Test message received for device {self.serial_number}: {event.get('message', '')}")
        await self.send(text_data=json.dumps({
            'type': 'test_message',
            'message': event.get('message', 'Test message'),
            'timestamp': event.get('timestamp', ''),
        }))
    
    async def analysis_complete(self, event):
        """Handle analysis completion events from Firebase Vision API"""
        logger.debug(f"Sending analysis_complete event to WebSocket for device {self.serial_number}")
        try:
            await self.send(text_data=json.dumps({
                'type': 'analysis_complete',
                'capture_id': event.get('capture_id'),
                'analysis_summary': event.get('analysis_summary', ''),
                'analysis_id': event.get('analysis_id'),
                'serial_number': self.serial_number
            }))
        except Exception as e:
            logger.error(f"Error sending analysis_complete to WebSocket for device {self.serial_number}: {str(e)}")
    
    @database_sync_to_async
    def get_device(self, serial_number, user_id):
        """Check if device exists and user owns it."""
        try:
            return Device.objects.get(serial_number=serial_number, owner_id=user_id)
        except Device.DoesNotExist:
            return None

