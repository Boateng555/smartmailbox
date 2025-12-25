# Firebase AI Setup Guide - Complete

Step-by-step guide to set up Firebase AI (Google Cloud Vision API) for mailbox analysis.

## Prerequisites

1. Google Cloud Platform (GCP) account
2. Credit card for billing (free tier available)
3. Domain configured (yourcamera.com)

## Step 1: Create Firebase/GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Create Project** or select existing project
3. Enter project name: `smart-mailbox` (or your preferred name)
4. Click **Create**
5. Wait for project creation (30-60 seconds)

## Step 2: Enable Billing

**Important**: Vision API requires billing to be enabled (even for free tier)

1. Go to **Billing** in GCP Console
2. Click **Link a billing account**
3. Add payment method (credit card)
4. Link to your project

**Note**: First 1,000 units/month are FREE. For ~300 mail detections/month, you'll stay in free tier.

## Step 3: Enable Cloud Vision API

1. In GCP Console, go to **APIs & Services** > **Library**
2. Search for **"Cloud Vision API"**
3. Click on **Cloud Vision API**
4. Click **Enable**
5. Wait for API to enable (1-2 minutes)

## Step 4: Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. **Service account details**:
   - Name: `smart-mailbox-vision`
   - Description: `Service account for Smart Mailbox Vision API`
   - Click **Create and Continue**
4. **Grant this service account access to project**:
   - Role: **Cloud Vision API User**
   - Click **Continue**
5. **Grant users access** (optional):
   - Skip or add your email
   - Click **Done**

## Step 5: Generate Service Account Key

1. Click on the service account you just created (`smart-mailbox-vision`)
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create**
6. JSON file will download automatically
7. **Save this file securely** - you'll need it for Django

## Step 6: Install Firebase Admin SDK

The required packages are already in `requirements.txt`:

```bash
cd django-webapp
pip install google-cloud-vision>=3.4.4 google-auth>=2.23.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 7: Configure Django

### Option A: Environment Variable (Recommended)

1. Upload service account JSON to your server
2. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

Or add to `.env.production`:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/opt/smartmailbox/google-credentials.json
```

### Option B: Docker Volume (For Docker Deployment)

1. Place JSON file in project directory (e.g., `django-webapp/google-credentials.json`)
2. Add to `docker-compose.prod.yml`:

```yaml
web:
  volumes:
    - ./google-credentials.json:/app/google-credentials.json:ro
```

3. Set environment variable:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json
```

### Option C: Django Settings (Alternative)

Add to `settings_production.py`:

```python
import os
GOOGLE_APPLICATION_CREDENTIALS = os.path.join(BASE_DIR, 'google-credentials.json')
```

## Step 8: Test the Integration

### Test in Django Shell

```bash
python manage.py shell
```

```python
from devices.firebase_vision import analyze_mail
import base64

# Load a test image
with open('test_image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Analyze
result = analyze_mail(image_data)
print(result)
# Expected output:
# {
#     "type": "package",
#     "size": "medium",
#     "carrier": "Amazon",
#     "confidence": 0.92,
#     "text": "extracted text...",
#     "carriers": ["Amazon"]
# }
```

### Test Individual Functions

```python
from devices.firebase_vision import detect_mail_type, read_text, detect_logos, estimate_size

# Test mail type detection
mail_type = detect_mail_type(image_data)
print(f"Mail type: {mail_type}")  # "package", "letter", or "envelope"

# Test text extraction
text = read_text(image_data)
print(f"Extracted text: {text}")

# Test logo detection
carriers = detect_logos(image_data)
print(f"Carriers: {carriers}")  # ["Amazon", "FedEx", "UPS"]

# Test size estimation
size = estimate_size(image_data)
print(f"Size: {size}")  # "small", "medium", or "large"
```

## Step 9: Verify in Production

1. Upload a capture from ESP32 device
2. Check Django logs for analysis results
3. Verify `CaptureAnalysis` record created in database
4. Check admin panel: `/admin/devices/captureanalysis/`

## Function Reference

### `detect_mail_type(image) -> str`

Detects mail type from image.

**Parameters:**
- `image`: Base64 encoded image string

**Returns:**
- `"package"` - Package/box detected
- `"letter"` - Letter/paper detected
- `"envelope"` - Envelope detected
- `"unknown"` - Unable to determine

**Example:**
```python
from devices.firebase_vision import detect_mail_type
mail_type = detect_mail_type(base64_image)
```

### `read_text(image) -> str`

Extracts visible text using OCR.

**Parameters:**
- `image`: Base64 encoded image string

**Returns:**
- Extracted text as string

**Example:**
```python
from devices.firebase_vision import read_text
text = read_text(base64_image)
```

### `detect_logos(image) -> list`

Detects shipping carrier logos.

**Parameters:**
- `image`: Base64 encoded image string

**Returns:**
- List of carrier names: `["Amazon", "FedEx", "UPS"]`

**Example:**
```python
from devices.firebase_vision import detect_logos
carriers = detect_logos(base64_image)
```

### `estimate_size(image) -> str`

Estimates mail item size.

**Parameters:**
- `image`: Base64 encoded image string

**Returns:**
- `"small"` - Small item (< 15% of image)
- `"medium"` - Medium item (15-40% of image)
- `"large"` - Large item (> 40% of image)
- `"unknown"` - Unable to determine

**Example:**
```python
from devices.firebase_vision import estimate_size
size = estimate_size(base64_image)
```

### `analyze_mail(image) -> dict`

Complete analysis with structured output.

**Parameters:**
- `image`: Base64 encoded image string

**Returns:**
```python
{
    "type": "package",           # "package", "letter", or "envelope"
    "size": "medium",            # "small", "medium", or "large"
    "carrier": "Amazon",         # Primary carrier or None
    "confidence": 0.92,          # 0.0 to 1.0
    "text": "extracted text...", # OCR text
    "carriers": ["Amazon"]       # All detected carriers
}
```

**Example:**
```python
from devices.firebase_vision import analyze_mail
result = analyze_mail(base64_image)
print(f"Type: {result['type']}, Size: {result['size']}, Carrier: {result['carrier']}")
```

## Troubleshooting

### "Vision API client not initialized"

**Solution:**
1. Check `GOOGLE_APPLICATION_CREDENTIALS` is set
2. Verify JSON file path is correct
3. Check file permissions (readable)
4. Verify JSON file is valid

### "Permission denied" or "403 Forbidden"

**Solution:**
1. Verify service account has "Cloud Vision API User" role
2. Check API is enabled in GCP Console
3. Verify billing is enabled

### "Billing not enabled"

**Solution:**
1. Go to GCP Console > Billing
2. Link billing account to project
3. Wait 5-10 minutes for changes to propagate

### Low Confidence Scores

**Possible causes:**
- Poor image quality
- Blurry images
- Low lighting
- Image too small

**Solutions:**
- Ensure ESP32 camera is properly focused
- Check lighting conditions
- Verify camera resolution settings

## Cost Monitoring

### Free Tier
- **First 1,000 units/month**: FREE
- Each image analysis = 1-5 units (depending on features)

### Pricing (after free tier)
- **1,001-5,000,000 units/month**: $1.50 per 1,000 units
- Example: 2,000 analyses/month = ~$1.50

### Monitor Usage
1. Go to GCP Console > Billing
2. Set up billing alerts
3. Review monthly usage reports

## Security Best Practices

1. **Never commit credentials**
   - Add `google-credentials.json` to `.gitignore`
   - Use environment variables

2. **Restrict service account permissions**
   - Only grant "Cloud Vision API User" role
   - Don't grant admin roles

3. **Rotate keys regularly**
   - Regenerate service account keys every 90 days
   - Update `GOOGLE_APPLICATION_CREDENTIALS` path

4. **Monitor usage**
   - Set up billing alerts
   - Review API usage logs
   - Check for unexpected spikes

5. **Use least privilege**
   - Service account should only have Vision API access
   - No other GCP service permissions needed

## Production Checklist

- [ ] GCP project created
- [ ] Billing enabled
- [ ] Cloud Vision API enabled
- [ ] Service account created with "Cloud Vision API User" role
- [ ] Service account key downloaded (JSON)
- [ ] Credentials file uploaded to server
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` environment variable set
- [ ] Dependencies installed (`google-cloud-vision`)
- [ ] Test analysis successful
- [ ] Production captures being analyzed
- [ ] Billing alerts configured
- [ ] Credentials file in `.gitignore`

## Next Steps

After setup:
1. Test with real mailbox captures
2. Monitor analysis accuracy
3. Adjust confidence thresholds if needed
4. Set up billing alerts
5. Review analysis results in admin panel







