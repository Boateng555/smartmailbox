# Notification System Setup Guide

This guide explains how to set up the complete notification system with email (SendGrid/SMTP) and push notifications.

## Features

1. **Email Notifications** with 3 photos attached
2. **Push Notifications** via web app
3. **Email Reply-to** for customer acknowledgments
4. **SendGrid Integration** for reliable email delivery

## Email Configuration

### Option 1: SendGrid (Recommended)

1. **Create SendGrid Account**
   - Sign up at [SendGrid](https://sendgrid.com/)
   - Verify your sender email/domain

2. **Get API Key**
   - Go to Settings > API Keys
   - Create a new API key with "Full Access" or "Mail Send" permissions
   - Copy the API key

3. **Configure Django**
   Add to your `.env` file:
   ```bash
   USE_SENDGRID=True
   SENDGRID_API_KEY=SG.your_api_key_here
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

4. **Set Up Inbound Parse (for email replies)**
   - Go to Settings > Inbound Parse
   - Add a new hostname (e.g., `mail.yourdomain.com`)
   - Set destination URL: `https://yourdomain.com/api/device/email/sendgrid-inbound/`
   - Add MX records to your DNS as instructed by SendGrid
   - This allows customers to reply to emails

### Option 2: SMTP (Gmail, etc.)

Add to your `.env` file:
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@smartmailbox.com
```

**Note:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### Option 3: AWS SES

Add to your `.env` file:
```bash
EMAIL_BACKEND=django_ses.SESBackend
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
```

## Push Notifications Setup

### 1. Generate VAPID Keys

VAPID keys are required for web push notifications. Generate them:

```bash
# Install web-push CLI
npm install -g web-push

# Generate keys
web-push generate-vapid-keys
```

This will output:
- Public Key (VAPID_PUBLIC_KEY)
- Private Key (VAPID_PRIVATE_KEY)

### 2. Configure Django

Add to your `.env` file:
```bash
VAPID_PUBLIC_KEY=your_public_key_here
VAPID_PRIVATE_KEY=your_private_key_here
```

Add to `settings.py`:
```python
VAPID_PUBLIC_KEY = config('VAPID_PUBLIC_KEY', default='')
VAPID_PRIVATE_KEY = config('VAPID_PRIVATE_KEY', default='')
```

### 3. Update Frontend Template

Make sure your base template includes the VAPID public key:

```html
<script>
    const VAPID_PUBLIC_KEY = '{{ VAPID_PUBLIC_KEY }}';
</script>
```

## Email Reply-to Setup

### How It Works

1. When mail is detected, an email is sent with reply-to address: `capture-{id}-{serial}@{domain}`
2. Customer replies to the email
3. Email webhook receives the reply
4. System parses the reply-to address to find the capture
5. Marks the capture as acknowledged

### SendGrid Inbound Parse

1. Configure Inbound Parse in SendGrid (see above)
2. Emails sent to `capture-*@yourdomain.com` will be forwarded to your webhook
3. Webhook endpoint: `/api/device/email/sendgrid-inbound/`

### Alternative: Manual Acknowledgment API

Customers can also acknowledge via API:

```bash
POST /api/device/capture/{capture_id}/acknowledge/
```

Requires authentication (user must own the device).

## Email Format

### Subject
```
📬 Mail Detected in Your Smart Mailbox
```

### Content
- HTML email with professional design
- AI analysis summary
- Timestamp
- Device information
- Battery status
- Door state

### Attachments
- 3 photos attached as JPEG files
- Photos from the same trigger event (within 10 seconds)

## Push Notification Format

### Title
```
📬 Mail Detected in Your Smart Mailbox
```

### Body
- AI analysis summary (e.g., "Large Amazon package detected")

### Actions
- "View Details" - Opens device page
- "Acknowledge" - Marks as acknowledged

## Testing

### Test Email

1. Trigger a capture from ESP32 device
2. Check email inbox for notification
3. Verify 3 photos are attached
4. Reply to email to test acknowledgment

### Test Push Notification

1. Open web app in browser
2. Allow push notification permissions
3. Trigger a capture
4. Verify push notification appears

### Test Email Reply

1. Send test email to: `capture-{id}-{serial}@yourdomain.com`
2. Check logs for webhook receipt
3. Verify capture is marked as acknowledged in admin

## Troubleshooting

### Email Not Sending

1. **Check API Key**: Verify SendGrid API key is correct
2. **Check Sender Verification**: SendGrid requires sender verification
3. **Check Logs**: Review Django logs for error messages
4. **Test SMTP**: Try SMTP backend to isolate SendGrid issues

### Push Notifications Not Working

1. **Check VAPID Keys**: Verify keys are set correctly
2. **Check Browser Permissions**: User must allow notifications
3. **Check Service Worker**: Ensure service worker is registered
4. **Check Subscription**: Verify subscription is saved in database

### Email Replies Not Working

1. **Check DNS**: Verify MX records for inbound parse
2. **Check Webhook URL**: Ensure URL is accessible
3. **Check Logs**: Review webhook logs for errors
4. **Test Manually**: Use API endpoint to test acknowledgment

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Webhook Security**: Consider adding authentication to webhook endpoints
3. **Email Validation**: Verify sender email matches device owner
4. **Rate Limiting**: Implement rate limiting for webhook endpoints

## Cost Considerations

### SendGrid
- Free tier: 100 emails/day
- Paid plans start at $19.95/month for 50,000 emails

### Push Notifications
- Free (uses browser push service)
- No additional cost

## Migration

Run migrations to add acknowledgment fields:

```bash
python manage.py migrate
```

This will add:
- `email_acknowledged` field to `CaptureAnalysis`
- `email_acknowledged_at` field to `CaptureAnalysis`







