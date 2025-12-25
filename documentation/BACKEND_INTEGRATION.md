# Backend Integration - ChatGPT Vision API & Subscription Logic

## Overview

This document describes the backend integration for ChatGPT Vision API, manual trigger endpoints, and subscription/click limit management.

## API Endpoints

### 1. POST /api/device/capture/ (Updated)

**Purpose:** Receive photos from ESP32-CAM

**Request:**
```json
{
  "serial_number": "ESP-12345",
  "image": "base64_encoded_image_string",
  "trigger_type": "automatic" | "manual",
  "battery_voltage": 3.85,
  "timestamp": 1234567890
}
```

**Response:**
```json
{
  "status": "saved",
  "capture_id": 123,
  "analysis_queued": true
}
```

**Flow:**
1. Save capture to database
2. Queue for ChatGPT Vision analysis
3. Return capture_id immediately
4. Process analysis asynchronously

### 2. POST /api/device/trigger/ (New)

**Purpose:** Manual trigger request from mobile app

**Request:**
```json
{
  "device_serial": "ESP-12345",
  "user_id": 123
}
```

**Response (Success):**
```json
{
  "status": "triggered",
  "trigger_id": 456,
  "message": "Device will capture photo on next wake cycle"
}
```

**Response (Click Limit Exceeded):**
```json
{
  "status": "error",
  "error": "click_limit_exceeded",
  "message": "You have reached your daily limit of 3 manual clicks",
  "clicks_used": 3,
  "clicks_limit": 3,
  "reset_at": "2024-01-02T00:00:00Z"
}
```

**Response (Device Offline):**
```json
{
  "status": "queued",
  "trigger_id": 456,
  "message": "Device is offline. Request queued for next wake cycle"
}
```

### 3. GET /api/device/status/

**Purpose:** Get device status and click limits

**Response:**
```json
{
  "device_serial": "ESP-12345",
  "status": "online" | "offline",
  "last_capture": "2024-01-01T12:00:00Z",
  "battery_voltage": 3.85,
  "user_tier": "free" | "premium",
  "clicks_used_today": 2,
  "clicks_limit": 3,
  "clicks_reset_at": "2024-01-02T00:00:00Z"
}
```

## Database Models

### ClickLimit Model

```python
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ClickLimit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.count} clicks"
    
    @classmethod
    def get_today_count(cls, user):
        """Get click count for today"""
        today = timezone.now().date()
        limit, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={'count': 0}
        )
        return limit.count
    
    @classmethod
    def increment(cls, user):
        """Increment click count for today"""
        today = timezone.now().date()
        limit, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={'count': 0}
        )
        limit.count += 1
        limit.save()
        return limit.count
    
    @classmethod
    def can_click(cls, user):
        """Check if user can make a manual click"""
        # Premium users have unlimited clicks
        if hasattr(user, 'subscription') and user.subscription.is_active:
            return True, None
        
        # Free users: 3 clicks per day
        count = cls.get_today_count(user)
        limit = 3
        
        if count >= limit:
            # Calculate reset time (midnight user's timezone)
            from django.utils import timezone
            now = timezone.now()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
            return False, {
                'clicks_used': count,
                'clicks_limit': limit,
                'reset_at': tomorrow.isoformat()
            }
        
        return True, None
```

### User Subscription Model

```python
from django.db import models
from django.contrib.auth.models import User

class Subscription(models.Model):
    TIER_FREE = 'free'
    TIER_PREMIUM = 'premium'
    TIER_CHOICES = [
        (TIER_FREE, 'Free'),
        (TIER_PREMIUM, 'Premium'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default=TIER_FREE)
    is_active = models.BooleanField(default=False)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.tier}"
    
    @property
    def manual_click_limit(self):
        """Return manual click limit for this tier"""
        if self.tier == self.TIER_PREMIUM and self.is_active:
            return None  # Unlimited
        return 3  # Free tier
```

## Manual Trigger Endpoint Implementation

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Device, ClickLimit, Subscription
from .serializers import TriggerRequestSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_trigger(request):
    """
    Manual trigger endpoint for mobile app.
    Validates click limits and queues trigger request.
    """
    serializer = TriggerRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    device_serial = serializer.validated_data['device_serial']
    user = request.user
    
    try:
        # Get device
        device = Device.objects.get(serial_number=device_serial)
        
        # Verify device ownership
        if device.owner != user:
            return Response(
                {'error': 'Device not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check click limits
        can_click, limit_info = ClickLimit.can_click(user)
        
        if not can_click:
            return Response(
                {
                    'status': 'error',
                    'error': 'click_limit_exceeded',
                    'message': f'You have reached your daily limit of {limit_info["clicks_limit"]} manual clicks',
                    'clicks_used': limit_info['clicks_used'],
                    'clicks_limit': limit_info['clicks_limit'],
                    'reset_at': limit_info['reset_at']
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        # Increment click count (for free users)
        subscription = getattr(user, 'subscription', None)
        if not (subscription and subscription.is_active and subscription.tier == Subscription.TIER_PREMIUM):
            ClickLimit.increment(user)
        
        # Check if device is online
        if device.status == 'offline':
            # Queue trigger for next wake cycle
            # Store in database or cache
            trigger_id = queue_manual_trigger(device, user)
            
            return Response(
                {
                    'status': 'queued',
                    'trigger_id': trigger_id,
                    'message': 'Device is offline. Request queued for next wake cycle'
                },
                status=status.HTTP_202_ACCEPTED
            )
        
        # Device is online - send immediate trigger (if cellular enabled)
        # For WiFi-only devices, queue for next wake
        trigger_id = queue_manual_trigger(device, user)
        
        return Response(
            {
                'status': 'triggered',
                'trigger_id': trigger_id,
                'message': 'Device will capture photo on next wake cycle'
            },
            status=status.HTTP_200_OK
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


def queue_manual_trigger(device, user):
    """Queue manual trigger request"""
    from .models import ManualTrigger
    
    trigger = ManualTrigger.objects.create(
        device=device,
        requested_by=user,
        status='pending'
    )
    
    logger.info(f"Manual trigger queued: {trigger.id} for device {device.serial_number}")
    return trigger.id
```

## ChatGPT Vision API Integration

### ChatGPT Vision Service

```python
import openai
import base64
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatGPTVisionService:
    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        openai.api_key = self.api_key
        self.model = "gpt-4-vision-preview"
    
    def analyze_mailbox_image(self, image_base64: str) -> dict:
        """
        Analyze mailbox image using ChatGPT Vision API.
        
        Args:
            image_base64: Base64-encoded image string
            
        Returns:
            {
                "mail_detected": bool,
                "confidence": float (0.0-1.0),
                "description": str,
                "items": list of detected items
            }
        """
        try:
            # Prepare prompt
            prompt = """Analyze this mailbox image. Determine if there is mail 
            (letters, packages, envelopes, postcards) present in the mailbox.
            
            Respond with a JSON object in this exact format:
            {
                "mail_detected": true or false,
                "confidence": 0.0 to 1.0,
                "description": "brief description of what you see",
                "items": ["list", "of", "detected", "items"]
            }
            
            Be accurate and conservative. Only report mail_detected=true if you 
            can clearly see mail items."""
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.1  # Low temperature for consistent results
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response (may be wrapped in markdown)
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire content
                result = json.loads(content)
            
            # Validate result
            if 'mail_detected' not in result:
                raise ValueError("Invalid response format from ChatGPT")
            
            logger.info(f"ChatGPT analysis: mail_detected={result['mail_detected']}, confidence={result.get('confidence', 0)}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ChatGPT response: {str(e)}")
            return {
                "mail_detected": False,
                "confidence": 0.0,
                "description": "Analysis failed: Invalid response format",
                "items": []
            }
        except Exception as e:
            logger.error(f"ChatGPT Vision API error: {str(e)}", exc_info=True)
            return {
                "mail_detected": False,
                "confidence": 0.0,
                "description": f"Analysis failed: {str(e)}",
                "items": []
            }


# Singleton instance
_vision_service = None

def get_chatgpt_vision_service():
    """Get or create ChatGPT Vision service instance"""
    global _vision_service
    if _vision_service is None:
        _vision_service = ChatGPTVisionService()
    return _vision_service
```

### Updated Capture Analysis

```python
def analyze_capture_with_chatgpt(capture: Capture):
    """
    Analyze capture using ChatGPT Vision API.
    """
    try:
        vision_service = get_chatgpt_vision_service()
        
        # Analyze image
        analysis_result = vision_service.analyze_mailbox_image(capture.image_base64)
        
        # Create CaptureAnalysis record
        analysis = CaptureAnalysis.objects.create(
            capture=capture,
            summary=analysis_result.get('description', 'Mailbox analyzed'),
            mail_detected=analysis_result.get('mail_detected', False),
            confidence_score=analysis_result.get('confidence', 0.0),
            detected_objects=analysis_result.get('items', []),
            processing_time_ms=None  # Can track if needed
        )
        
        logger.info(f"ChatGPT analysis completed for capture {capture.id}: "
                   f"mail_detected={analysis.mail_detected}, "
                   f"confidence={analysis.confidence_score}")
        
        # Send notification based on result
        if analysis.mail_detected:
            send_mail_detected_notification(capture, analysis)
        else:
            send_mailbox_empty_notification(capture, analysis)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing capture {capture.id}: {str(e)}", exc_info=True)
        return None
```

## Notification Flow

### Notification Service

```python
def send_mail_detected_notification(capture: Capture, analysis: CaptureAnalysis):
    """Send notification when mail is detected"""
    device = capture.device
    user = device.owner
    
    # Push notification
    send_push_notification(
        user=user,
        title="📬 Mail Detected",
        body=analysis.summary or "New mail in your mailbox",
        data={
            'capture_id': capture.id,
            'analysis_id': analysis.id,
            'mail_detected': True
        }
    )
    
    # Email notification (if enabled)
    if should_send_email_notification(user):
        send_email_notification(capture, analysis, mail_detected=True)
    
    # SMS notification (if enabled)
    if should_send_sms_notification(user):
        send_sms_notification(user, "📬 Mail detected in your mailbox!")


def send_mailbox_empty_notification(capture: Capture, analysis: CaptureAnalysis):
    """Send notification when mailbox is empty"""
    device = capture.device
    user = device.owner
    
    # Push notification (optional - may want to skip for empty)
    if user.notification_preferences.notify_on_empty:
        send_push_notification(
            user=user,
            title="📭 Mailbox Empty",
            body="Your mailbox is empty",
            data={
                'capture_id': capture.id,
                'analysis_id': analysis.id,
                'mail_detected': False
            }
        )
```

## Settings Configuration

```python
# settings.py

# OpenAI ChatGPT Vision API
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = 'gpt-4-vision-preview'

# Click limits
FREE_USER_CLICK_LIMIT = 3  # per day
PREMIUM_USER_CLICK_LIMIT = None  # unlimited

# Notification settings
ENABLE_PUSH_NOTIFICATIONS = True
ENABLE_EMAIL_NOTIFICATIONS = True
ENABLE_SMS_NOTIFICATIONS = True
```

## Error Handling

### ChatGPT API Errors

```python
def analyze_with_retry(capture: Capture, max_retries=3):
    """Analyze with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return analyze_capture_with_chatgpt(capture)
        except openai.error.RateLimitError:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
            time.sleep(wait_time)
        except openai.error.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            if attempt == max_retries - 1:
                # Final attempt failed
                return None
            time.sleep(2 ** attempt)
    return None
```

## Testing

### Test ChatGPT Integration

```python
# tests/test_chatgpt_vision.py

from django.test import TestCase
from devices.chatgpt_vision import get_chatgpt_vision_service

class ChatGPTVisionTestCase(TestCase):
    def test_analyze_mailbox_image(self):
        service = get_chatgpt_vision_service()
        
        # Load test image
        with open('test_images/mailbox_with_mail.jpg', 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        result = service.analyze_mailbox_image(image_base64)
        
        self.assertIn('mail_detected', result)
        self.assertIn('confidence', result)
        self.assertIn('description', result)
        self.assertIsInstance(result['mail_detected'], bool)
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)
```

## Cost Estimation

### ChatGPT Vision API Costs

- **GPT-4 Vision**: ~$0.01-0.03 per image
- **12 automatic captures/day**: $0.12-0.36/day
- **3 manual clicks/day (free)**: $0.03-0.09/day
- **Monthly cost per device**: ~$4.50-13.50/month

### Optimization

1. **Cache results** for similar images
2. **Batch processing** during off-peak hours
3. **Lower resolution** images (if acceptable)
4. **Skip analysis** for obviously empty mailboxes (optional)


