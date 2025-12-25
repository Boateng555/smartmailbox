"""
SMS notification service using Twilio.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms_notification(phone_number, message, capture_id=None):
    """
    Send SMS notification via Twilio.
    
    Args:
        phone_number: Recipient phone number (E.164 format: +1234567890)
        message: SMS message text
        capture_id: Optional capture ID for tracking
    
    Returns:
        bool: True if SMS sent successfully
    """
    try:
        from twilio.rest import Client
        
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        if not all([account_sid, auth_token, from_number]):
            logger.warning("Twilio not configured. SMS notifications disabled.")
            return False
        
        client = Client(account_sid, auth_token)
        
        # Send SMS
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        
        if message_obj.sid:
            logger.info(f"SMS sent successfully to {phone_number} (SID: {message_obj.sid})")
            if capture_id:
                logger.info(f"SMS sent for capture {capture_id}")
            return True
        else:
            logger.error(f"Failed to send SMS to {phone_number}")
            return False
            
    except ImportError:
        logger.warning("Twilio library not installed. Install with: pip install twilio")
        return False
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {str(e)}", exc_info=True)
        return False


def send_mail_detection_sms(phone_number, capture, analysis):
    """
    Send SMS notification for mail detection.
    
    Args:
        phone_number: Recipient phone number
        capture: Capture instance
        analysis: CaptureAnalysis instance
    
    Returns:
        bool: True if SMS sent successfully
    """
    # Build SMS message (max 160 characters for single SMS)
    device_serial = capture.device.serial_number
    summary = analysis.summary or "Mail detected"
    
    # Truncate summary if too long
    if len(summary) > 80:
        summary = summary[:77] + "..."
    
    message = f"📬 Mail: {summary} | Device: {device_serial[:8]} | View: {settings.API_DOMAIN}/device/{device_serial}/"
    
    # If message is too long, split into multiple parts
    if len(message) > 160:
        # Send shorter version
        message = f"📬 {summary} | {settings.API_DOMAIN}/device/{device_serial}/"
    
    return send_sms_notification(phone_number, message, capture.id)







