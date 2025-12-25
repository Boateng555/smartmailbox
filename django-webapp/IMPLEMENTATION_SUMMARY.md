# Django Backend with Firebase Vision API - Implementation Summary

## Overview

The Django backend has been enhanced with Firebase Vision API integration for analyzing mailbox captures. When photos are received from ESP32 devices, they are automatically analyzed to detect packages, letters, envelopes, extract text (OCR), identify logos, and estimate sizes.

## Features Implemented

### 1. Firebase Vision API Integration

- **Service**: `devices/firebase_vision.py`
  - Object detection (packages, letters, envelopes)
  - Text OCR (return addresses, shipping labels)
  - Logo/brand detection (Amazon, UPS, FedEx, USPS, DHL)
  - Size estimation (Large, Medium, Small)
  - Summary generation ("Large Amazon package detected")

### 2. Database Models

- **CaptureAnalysis Model** (`devices/models.py`)
  - Stores all analysis results from Firebase Vision
  - Tracks detected objects, text, logos, sizes
  - Records email notification status
  - Links to Capture via OneToOne relationship

- **Capture Model Updates**
  - Added `door_open` field (reed switch state)
  - Added `battery_voltage` field
  - Added `solar_charging` field

### 3. API Endpoint Updates

- **`/api/device/capture/`** (`devices/api_views.py`)
  - Now accepts additional fields: `door_open`, `battery_voltage`, `solar_charging`
  - Automatically triggers Firebase Vision analysis after saving capture
  - Creates `CaptureAnalysis` record with results
  - Sends email notifications to device owner

### 4. Email Notifications

- **Service**: `devices/email_service.py`
  - Sends HTML email when mail is detected
  - Includes analysis summary, detected items, brands, addresses
  - Configurable via Django settings (SMTP or AWS SES)

- **Email Template**: `devices/templates/devices/email/mail_detected.html`
  - Professional HTML email design
  - Shows summary, device info, detected items, battery status

### 5. WebSocket Integration

- **Consumer Update**: `web/consumers.py`
  - Added `analysis_complete` event handler
  - Broadcasts analysis results to connected clients in real-time

### 6. Admin Interface

- **CaptureAnalysis Admin** (`devices/admin.py`)
  - Full admin interface for viewing analysis results
  - Filterable by detection type, email status
  - Searchable by summary and detected text

## Configuration

### Environment Variables

```bash
# Firebase Vision API
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@smartmailbox.com
```

See `FIREBASE_SETUP.md` for detailed setup instructions.

## API Request Format

ESP32 devices should send POST requests to `/api/device/capture/` with:

```json
{
  "serial": "ESP-123456",
  "image": "base64_encoded_image_string",
  "motion_detected": true,
  "door_open": false,
  "battery_voltage": 3.8,
  "solar_charging": true,
  "connection_type": "wifi"
}
```

## Response Format

```json
{
  "status": "saved",
  "capture_id": 123
}
```

## Analysis Flow

1. **Capture Received**: ESP32 sends photo to `/api/device/capture/`
2. **Capture Saved**: Photo saved to database with metadata
3. **Analysis Triggered**: `analyze_capture_async()` called
4. **Firebase Vision**: Image analyzed for objects, text, logos
5. **Analysis Saved**: Results stored in `CaptureAnalysis` model
6. **Email Sent**: Notification sent to device owner
7. **WebSocket Broadcast**: Analysis results sent to connected clients

## Database Schema

### Capture Model
- `device` (ForeignKey)
- `timestamp` (DateTime)
- `image_base64` (Text)
- `motion_detected` (Boolean)
- `door_open` (Boolean) - NEW
- `battery_voltage` (Float) - NEW
- `solar_charging` (Boolean) - NEW

### CaptureAnalysis Model
- `capture` (OneToOne to Capture)
- `summary` (CharField) - e.g., "Large Amazon package detected"
- `detected_objects` (JSONField)
- `package_detected` (Boolean)
- `letter_detected` (Boolean)
- `envelope_detected` (Boolean)
- `detected_text` (TextField) - OCR results
- `return_addresses` (JSONField)
- `logos_detected` (JSONField)
- `estimated_size` (CharField) - "Large", "Medium", "Small"
- `bounding_boxes` (JSONField)
- `confidence_score` (Float)
- `processing_time_ms` (Integer)
- `email_sent` (Boolean)
- `email_sent_at` (DateTime)

## Migration

Run migrations to create new models and fields:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Testing

1. **Test Capture Upload**:
   ```bash
   curl -X POST http://localhost:8000/api/device/capture/ \
     -H "Content-Type: application/json" \
     -d '{
       "serial": "ESP-TEST-001",
       "image": "base64_image_here",
       "motion_detected": true
     }'
   ```

2. **Check Analysis**:
   - View in Django admin: `/admin/devices/captureanalysis/`
   - Check email inbox for notifications
   - Monitor WebSocket for real-time updates

## Error Handling

- Vision API errors are logged but don't fail the capture save
- Email failures are logged but don't block analysis
- WebSocket errors are logged but don't affect analysis
- All errors include full stack traces in logs

## Performance Considerations

- Analysis runs synchronously (consider Celery for production)
- Each analysis takes ~1-3 seconds
- Email sending is synchronous (consider async for production)
- WebSocket broadcasts are async and non-blocking

## Future Enhancements

- [ ] Add Celery for async task processing
- [ ] Add retry logic for failed analyses
- [ ] Add analysis caching for similar images
- [ ] Add batch processing for multiple captures
- [ ] Add webhook support for external integrations
- [ ] Add SMS notifications as alternative to email
- [ ] Add push notifications via Firebase Cloud Messaging







