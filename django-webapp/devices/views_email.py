"""
Email webhook views for handling incoming email replies.
Supports SendGrid Inbound Parse and other email webhook services.
"""
import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from .email_reply_handler import handle_email_reply, parse_reply_to_email
from .models import Capture, CaptureAnalysis

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def sendgrid_inbound_webhook(request):
    """
    Handle SendGrid Inbound Parse webhook for email replies.
    
    SendGrid Inbound Parse sends emails as POST data with form fields:
    - from: Sender email
    - to: Recipient email (reply-to address)
    - subject: Email subject
    - text: Plain text body
    - html: HTML body (optional)
    - envelope: JSON with additional info
    
    Configure in SendGrid:
    1. Go to Settings > Inbound Parse
    2. Add hostname and URL: https://yourdomain.com/api/email/sendgrid-inbound/
    3. SendGrid will POST to this endpoint when emails arrive
    """
    try:
        # Get email data from POST
        email_from = request.POST.get('from', '')
        email_to = request.POST.get('to', '')
        email_subject = request.POST.get('subject', '')
        email_body = request.POST.get('text', '') or request.POST.get('html', '')
        
        # Get envelope data if available
        envelope_str = request.POST.get('envelope', '{}')
        try:
            envelope = json.loads(envelope_str)
        except:
            envelope = {}
        
        logger.info(f"SendGrid inbound email received: from={email_from}, to={email_to}, subject={email_subject}")
        
        # Verify it's a reply-to our system
        capture_id, device_serial = parse_reply_to_email(email_to)
        if not capture_id:
            logger.info(f"Email to {email_to} is not a reply-to address, ignoring")
            return HttpResponse("OK", status=200)  # Still return OK to SendGrid
        
        # Handle the email reply
        success = handle_email_reply(email_from, email_to, email_subject, email_body)
        
        if success:
            logger.info(f"Email reply processed successfully for capture {capture_id}")
            return HttpResponse("OK", status=200)
        else:
            logger.warning(f"Failed to process email reply for capture {capture_id}")
            return HttpResponse("OK", status=200)  # Return OK anyway to avoid retries
        
    except Exception as e:
        logger.error(f"Error processing SendGrid inbound webhook: {str(e)}", exc_info=True)
        return HttpResponse("Error", status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generic_email_webhook(request):
    """
    Generic email webhook handler for other services (AWS SES, Mailgun, etc.)
    
    Accepts JSON payload:
    {
        "from": "user@example.com",
        "to": "capture-123-ESP-123456@smartmailbox.com",
        "subject": "Re: Mail Detected",
        "body": "Thanks, I got it!"
    }
    """
    try:
        # Try to get JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Fall back to form data
            data = {
                'from': request.POST.get('from', ''),
                'to': request.POST.get('to', ''),
                'subject': request.POST.get('subject', ''),
                'body': request.POST.get('body', '') or request.POST.get('text', ''),
            }
        
        email_from = data.get('from', '')
        email_to = data.get('to', '')
        email_subject = data.get('subject', '')
        email_body = data.get('body', '')
        
        logger.info(f"Generic email webhook received: from={email_from}, to={email_to}")
        
        # Verify it's a reply-to our system
        capture_id, device_serial = parse_reply_to_email(email_to)
        if not capture_id:
            logger.info(f"Email to {email_to} is not a reply-to address, ignoring")
            return JsonResponse({'status': 'ignored'}, status=200)
        
        # Handle the email reply
        success = handle_email_reply(email_from, email_to, email_subject, email_body)
        
        if success:
            return JsonResponse({'status': 'processed', 'capture_id': capture_id})
        else:
            return JsonResponse({'status': 'failed'}, status=400)
        
    except Exception as e:
        logger.error(f"Error processing generic email webhook: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_capture_api(request, capture_id):
    """
    API endpoint to manually acknowledge a capture (alternative to email reply).
    
    POST /api/device/capture/{capture_id}/acknowledge/
    """
    try:
        # Get capture and analysis
        try:
            capture = Capture.objects.get(id=capture_id)
            analysis = CaptureAnalysis.objects.get(capture=capture)
        except Capture.DoesNotExist:
            return JsonResponse({'error': 'Capture not found'}, status=404)
        except CaptureAnalysis.DoesNotExist:
            return JsonResponse({'error': 'Analysis not found'}, status=404)
        
        # Verify user owns the device (if authenticated)
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user != capture.device.owner:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Mark as acknowledged
        if not analysis.email_acknowledged:
            analysis.email_acknowledged = True
            analysis.email_acknowledged_at = timezone.now()
            analysis.save(update_fields=['email_acknowledged', 'email_acknowledged_at'])
            
            username = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'
            logger.info(f"Capture {capture_id} acknowledged via API by {username}")
            
            return JsonResponse({
                'status': 'acknowledged',
                'capture_id': capture_id,
                'acknowledged_at': analysis.email_acknowledged_at.isoformat()
            })
        else:
            return JsonResponse({
                'status': 'already_acknowledged',
                'capture_id': capture_id,
                'acknowledged_at': analysis.email_acknowledged_at.isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error acknowledging capture {capture_id}: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

