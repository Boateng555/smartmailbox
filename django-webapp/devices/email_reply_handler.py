"""
Email reply handler for customer acknowledgments.
Handles incoming emails sent to reply-to addresses.
"""
import logging
import re
from django.utils import timezone
from django.conf import settings
from .models import Capture, CaptureAnalysis

logger = logging.getLogger(__name__)


def parse_reply_to_email(email_address):
    """
    Parse reply-to email address to extract capture ID and device serial.
    
    Format: capture-{capture_id}-{device_serial}@{domain}
    Example: capture-123-ESP-123456@smartmailbox.com
    
    Returns:
        tuple: (capture_id, device_serial) or (None, None) if parsing fails
    """
    try:
        # Extract local part (before @)
        local_part = email_address.split('@')[0]
        
        # Match pattern: capture-{id}-{serial}
        match = re.match(r'capture-(\d+)-(.+)', local_part)
        if match:
            capture_id = int(match.group(1))
            device_serial = match.group(2)
            return capture_id, device_serial
        
        return None, None
    except Exception as e:
        logger.error(f"Failed to parse reply-to email {email_address}: {str(e)}")
        return None, None


def handle_email_reply(email_from, email_to, email_subject, email_body):
    """
    Handle incoming email reply for acknowledgment.
    
    This function should be called by your email webhook handler
    (SendGrid Inbound Parse, AWS SES, or similar).
    
    Args:
        email_from: Sender email address
        email_to: Recipient email address (reply-to address)
        email_subject: Email subject
        email_body: Email body text
        
    Returns:
        bool: True if acknowledgment was processed, False otherwise
    """
    try:
        # Parse reply-to address to get capture info
        capture_id, device_serial = parse_reply_to_email(email_to)
        
        if not capture_id:
            logger.warning(f"Could not parse capture ID from reply-to: {email_to}")
            return False
        
        # Get capture and analysis
        try:
            capture = Capture.objects.get(id=capture_id)
            analysis = CaptureAnalysis.objects.get(capture=capture)
        except Capture.DoesNotExist:
            logger.warning(f"Capture {capture_id} not found for email reply")
            return False
        except CaptureAnalysis.DoesNotExist:
            logger.warning(f"Analysis not found for capture {capture_id}")
            return False
        
        # Verify device serial matches
        if capture.device.serial_number != device_serial:
            logger.warning(f"Device serial mismatch: expected {device_serial}, got {capture.device.serial_number}")
            return False
        
        # Check if user email matches device owner
        device_owner = capture.device.owner
        if device_owner.email.lower() != email_from.lower():
            logger.warning(f"Email from {email_from} does not match device owner {device_owner.email}")
            # Still allow acknowledgment - might be from different email
            # return False
        
        # Mark as acknowledged
        if not analysis.email_acknowledged:
            analysis.email_acknowledged = True
            analysis.email_acknowledged_at = timezone.now()
            analysis.save(update_fields=['email_acknowledged', 'email_acknowledged_at'])
            
            logger.info(f"Email acknowledgment received for capture {capture_id} from {email_from}")
            
            # Optionally send confirmation email
            send_acknowledgment_confirmation(capture, analysis, email_from)
            
            return True
        else:
            logger.info(f"Capture {capture_id} already acknowledged")
            return True
        
    except Exception as e:
        logger.error(f"Error handling email reply: {str(e)}", exc_info=True)
        return False


def send_acknowledgment_confirmation(capture, analysis, user_email):
    """
    Send confirmation email when acknowledgment is received.
    """
    try:
        from django.core.mail import send_mail
        
        subject = "✓ Mail Acknowledged"
        message = f"""
Thank you for acknowledging the mail detection.

Capture ID: {capture.id}
Detected: {analysis.summary}
Time: {capture.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Your acknowledgment has been recorded.
        """.strip()
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartmailbox.com')
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user_email],
            fail_silently=True,
        )
        
        logger.info(f"Acknowledgment confirmation sent to {user_email}")
        
    except Exception as e:
        logger.error(f"Failed to send acknowledgment confirmation: {str(e)}")







