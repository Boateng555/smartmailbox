# Complete Notification System for Mail Detection

Comprehensive notification system with email, SMS, push notifications, customer preferences, and data optimization.

## Features Implemented

### 1. Real-Time Alerts ✅

#### Email Notifications
- **Subject**: "📬 Mail in Your Smart Mailbox"
- **3 Photos Attached**: Thumbnails (<100KB each) for email
- **AI Analysis**: Package/letter/size/carrier information
- **Timestamp**: Time detected
- **View Link**: Link to full resolution photos in web app
- **Reply-to**: Customers can reply to acknowledge

#### SMS Notifications (Twilio)
- **Format**: "📬 Mail: {summary} | Device: {serial} | View: {url}"
- **Max 160 characters**: Optimized for single SMS
- **E.164 Format**: Phone numbers in international format (+1234567890)
- **Optional**: Can be enabled per user

#### Push Notifications
- **Title**: "📬 Mail Detected in Your Smart Mailbox"
- **Body**: AI analysis summary
- **Actions**: "View Details" and "Acknowledge" buttons
- **Real-time**: Sent immediately (not affected by quiet hours)

### 2. Email Template ✅

**Subject**: "📬 Mail in Your Smart Mailbox"

**Body Includes**:
- Time detected (formatted)
- Device serial number
- AI analysis summary
- Mail type (package/letter/envelope)
- Mail size (small/medium/large)
- Carrier (Amazon, FedEx, UPS, etc.)
- 3 thumbnail photos attached
- Link to view full resolution photos
- Reply-to for acknowledgment

**Template**: `devices/templates/devices/email/mail_detected.html`

### 3. Data Usage Optimization ✅

#### Thumbnail Generation
- **Email Photos**: Automatically resized to <100KB each
- **Quality**: JPEG quality 80 (adjustable)
- **Compression**: Optimized for email delivery
- **Total Size**: <300KB for 3 photos in email

#### Full Resolution
- **Web App**: Full resolution photos available
- **Download**: Customers can download full images
- **Storage**: Original images stored in database

#### Cellular Data Optimization
- **Configurable**: Thumbnail size per user preference
- **Default**: 100KB per photo
- **Total**: <500KB per notification sequence
- **Compression**: Automatic based on data plan

### 4. Customer Preferences ✅

#### Notification Channels
- **Email**: Enable/disable email notifications
- **SMS**: Enable/disable SMS notifications
- **Push**: Enable/disable push notifications

#### Notification Timing
- **Immediate**: Send notifications immediately when mail detected
- **Hourly Summaries**: (Future feature) Batch notifications hourly

#### Quiet Hours
- **Enabled**: Toggle quiet hours on/off
- **Start Time**: Default 10 PM (22:00)
- **End Time**: Default 7 AM (07:00)
- **Applies To**: Email and SMS (push notifications always sent)
- **Span Midnight**: Supports quiet hours that span midnight

#### Data Optimization
- **Thumbnail Size**: Configurable per user (default 100KB)
- **Cellular Plan**: Adjust based on data plan limits

## Database Models

### NotificationPreferences
```python
- user (OneToOne to User)
- email_enabled (Boolean, default=True)
- sms_enabled (Boolean, default=False)
- push_enabled (Boolean, default=True)
- immediate (Boolean, default=True)
- quiet_hours_start (Time, default=22:00)
- quiet_hours_end (Time, default=07:00)
- quiet_hours_enabled (Boolean, default=True)
- email_thumbnail_size (Integer, default=100 KB)
- phone_number (CharField, E.164 format)
```

## Configuration

### Email Setup
See `NOTIFICATION_SETUP.md` for complete email configuration.

### SMS Setup (Twilio)

1. **Create Twilio Account**
   - Sign up at [Twilio](https://www.twilio.com/)
   - Get phone number
   - Get Account SID and Auth Token

2. **Configure Django**
   Add to `.env`:
   ```bash
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio number
   ```

3. **Install Twilio**
   ```bash
   pip install twilio
   ```

### Push Notifications
See `NOTIFICATION_SETUP.md` for VAPID key setup.

## Usage

### Sending Notifications

Notifications are automatically sent when mail is detected:

```python
from devices.api_views import analyze_capture_async

# Called automatically when capture is uploaded
analyze_capture_async(capture)
```

### Checking Preferences

```python
from devices.notification_preferences import should_send_notification, get_notification_preferences

user = request.user

# Check if email should be sent
if should_send_notification(user, 'email'):
    send_email()

# Get full preferences
prefs = get_notification_preferences(user)
if prefs.is_quiet_hours():
    # Skip notification
    pass
```

### User Preferences API

Create API endpoints to manage preferences:

```python
# GET /api/user/preferences/
# POST /api/user/preferences/
# PATCH /api/user/preferences/
```

## Files Created/Modified

### New Files
- `devices/notification_preferences.py` - Preference management
- `devices/sms_service.py` - SMS notification service
- `devices/migrations/0010_notification_preferences.py` - Migration
- `devices/templates/devices/email/mail_detected.html` - Email template

### Modified Files
- `devices/email_service.py` - Added thumbnail generation
- `devices/api_views.py` - Added preference checking
- `devices/models.py` - Added NotificationPreferences model
- `requirements.txt` - Added twilio

## Email Template Features

- **Responsive Design**: Works on mobile and desktop
- **Professional Styling**: Clean, modern design
- **AI Analysis Display**: Shows mail type, size, carrier
- **Thumbnail Note**: Explains full resolution available in app
- **View Link**: Button to view full details
- **Reply-to**: Instructions for acknowledgment

## SMS Message Format

```
📬 Mail: Large Amazon package detected | Device: ESP-1234 | View: https://yourcamera.com/device/ESP-1234/
```

**Optimized for**:
- Single SMS (160 characters)
- Clear information
- Direct link to view details

## Quiet Hours Logic

```python
# Default: 10 PM to 7 AM
# Email and SMS: Blocked during quiet hours
# Push: Always sent (user can disable on device)
```

**Example**:
- Mail detected at 11 PM → Email/SMS blocked, Push sent
- Mail detected at 8 AM → All notifications sent

## Data Optimization

### Thumbnail Creation
- **Original**: Full resolution (may be 1-5MB)
- **Thumbnail**: <100KB (default)
- **Quality**: JPEG 80 (adjustable)
- **Method**: Resize + compress

### Total Email Size
- **3 Thumbnails**: ~300KB total
- **Email Body**: ~10KB
- **Total**: ~310KB per notification

### Cellular Data Savings
- **Without Optimization**: 3-15MB per notification
- **With Optimization**: ~310KB per notification
- **Savings**: ~95% reduction

## Future Enhancements

1. **Hourly Summaries**: Batch notifications hourly
2. **Custom Quiet Hours**: Per-device quiet hours
3. **Notification History**: Track sent notifications
4. **Delivery Status**: Track email/SMS delivery
5. **A/B Testing**: Test different notification formats

## Testing

### Test Email
```python
from devices.email_service import send_mail_notification
send_mail_notification(capture, analysis, related_captures)
```

### Test SMS
```python
from devices.sms_service import send_mail_detection_sms
send_mail_detection_sms("+1234567890", capture, analysis)
```

### Test Preferences
```python
from devices.notification_preferences import should_send_notification
should_send_notification(user, 'email')
```

## Summary

Complete notification system with:
- ✅ Email with thumbnails
- ✅ SMS via Twilio
- ✅ Push notifications
- ✅ Customer preferences
- ✅ Quiet hours
- ✅ Data optimization
- ✅ AI analysis integration
- ✅ Professional email template

All notifications respect user preferences and quiet hours, with optimized data usage for cellular connections.







