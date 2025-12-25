# Firebase Vision API Setup Guide

This guide explains how to set up Google Cloud Vision API (Firebase Vision) for the Smart Mailbox Django backend.

## Prerequisites

1. Google Cloud Platform (GCP) account
2. A GCP project with billing enabled
3. Vision API enabled in your project

## Step 1: Create a GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable billing for the project (Vision API requires billing)

## Step 2: Enable Vision API

1. Navigate to **APIs & Services** > **Library**
2. Search for "Cloud Vision API"
3. Click **Enable**

## Step 3: Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Enter a name (e.g., "smart-mailbox-vision")
4. Click **Create and Continue**
5. Grant the role: **Cloud Vision API User**
6. Click **Continue** and then **Done**

## Step 4: Generate Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Download the JSON file

## Step 5: Configure Django

### Option A: Environment Variable (Recommended for Production)

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your service account JSON file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Option B: Django Settings

Add to your `.env` file or environment:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Option C: Place in Project Directory (Development Only)

1. Place the JSON file in your project directory (e.g., `django-webapp/`)
2. Add to `.gitignore` to prevent committing credentials:
   ```
   *.json
   service-account-key.json
   ```
3. Update settings or environment variable to point to the file

## Step 6: Install Dependencies

The required packages are already in `requirements.txt`:

```bash
pip install google-cloud-vision google-auth
```

## Step 7: Test the Integration

1. Start your Django server
2. Upload a capture from your ESP32 device
3. Check the logs for Vision API analysis results
4. Verify that `CaptureAnalysis` records are created in the database

## Email Configuration

### SMTP (Gmail Example)

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

**Note:** For Gmail, you'll need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### AWS SES (Alternative)

```bash
EMAIL_BACKEND=django_ses.SESBackend
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
```

## Troubleshooting

### Vision API Not Working

1. **Check credentials path**: Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly
2. **Check API is enabled**: Ensure Vision API is enabled in your GCP project
3. **Check billing**: Ensure billing is enabled for your project
4. **Check service account permissions**: Verify the service account has "Cloud Vision API User" role
5. **Check logs**: Review Django logs for specific error messages

### Email Not Sending

1. **Check email settings**: Verify all email configuration variables are set
2. **Check SMTP credentials**: For Gmail, ensure you're using an App Password
3. **Check user email**: Ensure device owners have email addresses in their user profiles
4. **Check logs**: Review Django logs for email sending errors

## Cost Considerations

Google Cloud Vision API pricing (as of 2024):
- **First 1,000 units/month**: Free
- **1,001-5,000,000 units/month**: $1.50 per 1,000 units
- Each image analysis counts as 1-5 units depending on features used

For a mailbox that detects mail 10 times per day:
- ~300 analyses/month = Free tier

Monitor usage in [GCP Console](https://console.cloud.google.com/billing) to track costs.

## Security Best Practices

1. **Never commit credentials**: Always add service account keys to `.gitignore`
2. **Use environment variables**: Store credentials in environment variables, not in code
3. **Rotate keys regularly**: Periodically regenerate service account keys
4. **Limit permissions**: Only grant necessary permissions to service accounts
5. **Monitor usage**: Set up billing alerts in GCP Console







