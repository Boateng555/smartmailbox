"""
Email notification service for mailbox alerts.
Supports SendGrid, SMTP, and AWS SES.
Includes thumbnail generation for data optimization.
"""
import base64
import io
import logging
from PIL import Image
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import EmailMultiAlternatives, send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_mail_notification(capture, analysis, related_captures=None, thumbnail_size_kb=100):
    """
    Send email notification when mail is detected with 3 photos attached.
    
    Args:
        capture: Capture model instance (primary capture)
        analysis: CaptureAnalysis model instance
        related_captures: List of related Capture instances (for 3 photos total)
        thumbnail_size_kb: Maximum size per thumbnail in KB (default 100KB)
    """
    try:
        from .notification_preferences import should_send_notification, get_notification_preferences
        
        device = capture.device
        owner = device.owner
        
        # Check notification preferences
        if not should_send_notification(owner, 'email'):
            logger.info(f"Email notification skipped for {owner.username} (preferences or quiet hours)")
            return False
        
        # Get owner's email
        recipient_email = owner.email
        if not recipient_email:
            logger.warning(f"No email address for user {owner.username}, skipping notification")
            return False
        
        # Get thumbnail size from preferences
        prefs = get_notification_preferences(owner)
        thumbnail_size_kb = prefs.get_thumbnail_size()
        
        # Email subject - exact format requested
        subject = "📬 Mail in Your Smart Mailbox"
        
        # Get reply-to email (for acknowledgment)
        reply_to_email = get_reply_to_email(capture.id, device.serial_number)
        
        # Build view URL
        view_url = f"{getattr(settings, 'API_DOMAIN', 'https://yourcamera.com')}/device/{device.serial_number}/capture/{capture.id}/"
        
        # Email content with AI analysis
        context = {
            'device': device,
            'capture': capture,
            'analysis': analysis,
            'summary': analysis.summary,
            'timestamp': capture.timestamp,
            'reply_to_email': reply_to_email,
            'view_url': view_url,
            'mail_type': analysis.type if hasattr(analysis, 'type') else None,
            'mail_size': analysis.estimated_size if hasattr(analysis, 'estimated_size') else None,
            'carrier': analysis.carrier if hasattr(analysis, 'carrier') else None,
        }
        
        # Render HTML email
        html_message = render_to_string('devices/email/mail_detected.html', context)
        plain_message = strip_tags(html_message)
        
        # Get 3 photos to attach (as thumbnails)
        photos_to_attach = get_photos_for_email(capture, related_captures, thumbnail_size_kb)
        
        # Send email based on backend
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
        
        if 'sendgrid' in email_backend.lower() or getattr(settings, 'USE_SENDGRID', False):
            return send_via_sendgrid(
                recipient_email, subject, html_message, plain_message, 
                photos_to_attach, reply_to_email
            )
        else:
            return send_via_smtp(
                recipient_email, subject, html_message, plain_message,
                photos_to_attach, reply_to_email
            )
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}", exc_info=True)
        return False


def create_thumbnail(image_data, max_size_kb=100, quality=80):
    """
    Create thumbnail from image data, optimized for email.
    
    Args:
        image_data: Original image bytes
        max_size_kb: Maximum size in KB (default 100KB)
        quality: JPEG quality (1-100, default 80)
    
    Returns:
        bytes: Thumbnail image data
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Calculate target size to keep under max_size_kb
        original_size = len(image_data) / 1024  # KB
        target_size_kb = max_size_kb
        
        if original_size <= target_size_kb:
            # Image is already small enough, just re-encode with quality
            output = io.BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
        
        # Calculate scale factor to achieve target size
        # Size reduction is roughly quadratic with dimension reduction
        scale_factor = (target_size_kb / original_size) ** 0.5
        scale_factor = max(0.1, min(0.9, scale_factor))  # Limit between 10% and 90%
        
        # Calculate new dimensions
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)
        
        # Resize image
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Save with compression
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        thumbnail_data = output.getvalue()
        
        # If still too large, reduce quality further
        while len(thumbnail_data) / 1024 > target_size_kb and quality > 30:
            quality -= 10
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            thumbnail_data = output.getvalue()
        
        logger.info(f"Thumbnail created: {len(image_data)/1024:.1f}KB -> {len(thumbnail_data)/1024:.1f}KB")
        return thumbnail_data
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {str(e)}", exc_info=True)
        # Return original if thumbnail creation fails
        return image_data


def get_photos_for_email(primary_capture, related_captures=None, thumbnail_size_kb=100):
    """
    Get up to 3 photos for email attachment with thumbnails.
    Returns list of tuples: (image_data_bytes, filename, is_thumbnail)
    
    Args:
        primary_capture: Primary Capture instance
        related_captures: List of related Capture instances
        thumbnail_size_kb: Maximum size per thumbnail in KB (default 100KB)
    """
    photos = []
    
    # Add primary capture
    try:
        image_data = base64.b64decode(primary_capture.image_base64)
        thumbnail = create_thumbnail(image_data, max_size_kb=thumbnail_size_kb)
        photos.append((thumbnail, f"mailbox_photo_1_{primary_capture.id}.jpg", True))
    except Exception as e:
        logger.error(f"Failed to decode primary capture image: {str(e)}")
    
    # Add related captures if provided
    if related_captures:
        for idx, related_capture in enumerate(related_captures[:2], start=2):  # Max 2 more (total 3)
            try:
                image_data = base64.b64decode(related_capture.image_base64)
                thumbnail = create_thumbnail(image_data, max_size_kb=thumbnail_size_kb)
                photos.append((thumbnail, f"mailbox_photo_{idx}_{related_capture.id}.jpg", True))
            except Exception as e:
                logger.error(f"Failed to decode related capture image: {str(e)}")
    
    # If we don't have 3 photos yet, try to get recent captures from same device
    if len(photos) < 3:
        from .models import Capture
        recent_captures = Capture.objects.filter(
            device=primary_capture.device
        ).exclude(id=primary_capture.id).order_by('-timestamp')[:3-len(photos)]
        
        for idx, recent_capture in enumerate(recent_captures, start=len(photos)+1):
            try:
                image_data = base64.b64decode(recent_capture.image_base64)
                thumbnail = create_thumbnail(image_data, max_size_kb=thumbnail_size_kb)
                photos.append((thumbnail, f"mailbox_photo_{idx}_{recent_capture.id}.jpg", True))
                if len(photos) >= 3:
                    break
            except Exception as e:
                logger.error(f"Failed to decode recent capture image: {str(e)}")
    
    return photos


def get_reply_to_email(capture_id, device_serial):
    """
    Generate reply-to email address for acknowledgment.
    Format: capture-{id}@{domain} or acknowledge-{id}@{domain}
    """
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartmailbox.com')
    
    # Extract domain from from_email
    if '@' in from_email:
        domain = from_email.split('@')[1]
    else:
        domain = 'smartmailbox.com'
    
    # Generate reply-to address
    reply_to = f"capture-{capture_id}-{device_serial}@{domain}"
    
    # If using SendGrid, configure reply-to handling
    if getattr(settings, 'USE_SENDGRID', False):
        # SendGrid can handle reply-to via webhook
        return reply_to
    
    return reply_to


def send_via_sendgrid(recipient_email, subject, html_message, plain_message, photos, reply_to):
    """Send email via SendGrid API"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment
        
        api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        if not api_key:
            logger.error("SENDGRID_API_KEY not configured")
            return False
        
        sg = SendGridAPIClient(api_key=api_key)
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartmailbox.com')
        
        # Create email
        message = Mail(
            from_email=from_email,
            to_emails=recipient_email,
            subject=subject,
            html_content=html_message,
            plain_text_content=plain_message
        )
        
        # Set reply-to
        if reply_to:
            message.reply_to = reply_to
        
        # Attach photos
        for photo_data, filename in photos:
            encoded_photo = base64.b64encode(photo_data).decode()
            attachment = Attachment()
            attachment.file_content = encoded_photo
            attachment.file_type = "image/jpeg"
            attachment.file_name = filename
            attachment.disposition = "attachment"
            message.add_attachment(attachment)
        
        # Send email
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"SendGrid email sent successfully to {recipient_email}")
            return True
        else:
            logger.error(f"SendGrid email failed: {response.status_code} - {response.body}")
            return False
            
    except ImportError:
        logger.error("SendGrid library not installed. Install with: pip install sendgrid-django")
        return False
    except Exception as e:
        logger.error(f"Failed to send email via SendGrid: {str(e)}", exc_info=True)
        return False


def send_via_smtp(recipient_email, subject, html_message, plain_message, photos, reply_to):
    """Send email via SMTP with attachments"""
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartmailbox.com')
        
        # Create email message with attachments
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_email,
            to=[recipient_email],
            reply_to=[reply_to] if reply_to else None
        )
        
        # Attach HTML version
        email.attach_alternative(html_message, "text/html")
        
        # Attach photos
        for photo_data, filename in photos:
            email.attach(filename, photo_data, 'image/jpeg')
        
        # Send email
        email.send(fail_silently=False)
        
        logger.info(f"SMTP email sent successfully to {recipient_email} with {len(photos)} attachments")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {str(e)}", exc_info=True)
        return False


def send_mail_summary_email(capture, analysis):
    """
    Send a summary email with analysis details.
    Alternative simpler email format.
    """
    try:
        device = capture.device
        owner = device.owner
        
        recipient_email = owner.email
        if not recipient_email:
            return False
        
        subject = f"📬 New Mail: {analysis.summary}"
        
        # Build email body
        body_parts = [
            f"Mail detected in your smart mailbox ({device.serial_number})",
            "",
            f"Summary: {analysis.summary}",
            f"Time: {capture.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if analysis.detected_text:
            body_parts.append("")
            body_parts.append("Detected text:")
            body_parts.append(analysis.detected_text[:200])  # Limit text length
        
        if analysis.logos_detected:
            body_parts.append("")
            body_parts.append("Detected brands:")
            for logo in analysis.logos_detected[:3]:  # Top 3 logos
                body_parts.append(f"- {logo.get('description', 'Unknown')}")
        
        message = "\n".join(body_parts)
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartmailbox.com')
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        logger.info(f"Summary email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send summary email: {str(e)}", exc_info=True)
        return False

