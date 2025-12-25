# Smart Mailbox System - Complete Architecture

## System Overview

The Smart Mailbox System uses an ESP32-CAM that wakes up automatically every 2 hours or manually via a mobile app button. The device captures a photo, uploads it to a cloud server, which uses ChatGPT Vision API to detect mail presence. Results are sent to users via push notifications, with free users limited to 3 manual clicks per day.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER MOBILE APP                          │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  Manual Trigger  │         │  View Results    │              │
│  │     Button       │────────▶│   & Notifications│              │
│  └──────────────────┘         └──────────────────┘              │
│         │                                ▲                        │
│         │                                │                        │
│         │ POST /api/device/trigger/      │ Push Notification      │
│         │                                │                        │
└─────────┼────────────────────────────────┼────────────────────────┘
          │                                │
          ▼                                │
┌─────────────────────────────────────────┼────────────────────────┐
│              CLOUD SERVER (Django)       │                        │
│  ┌───────────────────────────────────────┼────────────────────┐  │
│  │  API Endpoints:                       │                    │  │
│  │  • POST /api/device/capture/         │                    │  │
│  │  • POST /api/device/trigger/         │                    │  │
│  │  • GET  /api/device/status/          │                    │  │
│  └───────────────────────────────────────┼────────────────────┘  │
│           │                              │                        │
│           │ Store Photo                  │                        │
│           ▼                              │                        │
│  ┌───────────────────────────────────────┼────────────────────┐  │
│  │  Database (PostgreSQL/SQLite)         │                    │  │
│  │  • Devices                            │                    │  │
│  │  • Captures                           │                    │  │
│  │  • Users & Subscriptions              │                    │  │
│  │  • Click Limits (Free: 3/day)         │                    │  │
│  └───────────────────────────────────────┼────────────────────┘  │
│           │                              │                        │
│           │ Send to AI                  │                        │
│           ▼                              │                        │
│  ┌───────────────────────────────────────┼────────────────────┐  │
│  │  ChatGPT Vision API Integration       │                    │  │
│  │  • Analyze image                      │                    │  │
│  │  • Detect mail presence               │                    │  │
│  │  • Return: "mail" or "empty"          │                    │  │
│  └───────────────────────────────────────┼────────────────────┘  │
│           │                              │                        │
│           │ Analysis Result               │                        │
│           ▼                              │                        │
│  ┌───────────────────────────────────────┼────────────────────┐  │
│  │  Notification Service                  │                    │  │
│  │  • Firebase Cloud Messaging (FCM)     │                    │  │
│  │  • Send push notification to app      │                    │  │
│  │  • Include analysis result            │                    │  │
│  └───────────────────────────────────────┼────────────────────┘  │
└───────────────────────────────────────────┼────────────────────────┘
                                             │
                                             │
┌────────────────────────────────────────────┼────────────────────────┐
│              ESP32-CAM DEVICE               │                        │
│  ┌─────────────────────────────────────────┼────────────────────┐  │
│  │  Wake Triggers:                         │                    │  │
│  │  1. Timer (every 2 hours)              │                    │  │
│  │  2. Manual (via API call)              │                    │  │
│  └─────────────────────────────────────────┼────────────────────┘  │
│           │                                │                        │
│           │ Wake from Deep Sleep           │                        │
│           ▼                                │                        │
│  ┌─────────────────────────────────────────┼────────────────────┐  │
│  │  Boot Sequence:                         │                    │  │
│  │  1. Initialize camera                   │                    │  │
│  │  2. Connect to WiFi/Cellular            │                    │  │
│  │  3. Capture photo                       │                    │  │
│  │  4. Upload to server                    │                    │  │
│  │  5. Return to deep sleep                │                    │  │
│  └─────────────────────────────────────────┼────────────────────┘  │
│           │                                │                        │
│           │ POST /api/device/capture/      │                        │
│           │ {serial, image, trigger_type} │                        │
│           ▼                                │                        │
└───────────┼────────────────────────────────┼────────────────────────┘
            │                                │
            └────────────────────────────────┘
```

## Detailed Flow Diagrams

### Flow 1: Automatic Timer-Based Capture (Every 2 Hours)

```
ESP32-CAM (Deep Sleep)
    │
    │ Timer expires (2 hours)
    ▼
Wake from Deep Sleep
    │
    │ Initialize (2-3 seconds)
    ▼
Connect to WiFi/Cellular (5-10 seconds)
    │
    │ Camera ready
    ▼
Capture Photo (1-2 seconds)
    │
    │ Base64 encode
    ▼
Upload to Server (3-5 seconds)
    POST /api/device/capture/
    {
      "serial_number": "ESP-12345",
      "image": "base64...",
      "trigger_type": "automatic"
    }
    │
    │ Server receives
    ▼
Server stores in database
    │
    │ Queue for AI analysis
    ▼
ChatGPT Vision API
    │
    │ Analyze image
    ▼
Return: {"mail_detected": true/false, "confidence": 0.95}
    │
    │ Store result
    ▼
Send Push Notification
    │
    │ FCM to user's device
    ▼
User receives notification
    "📬 Mail detected in your mailbox!"
    or
    "📭 Mailbox is empty"
    │
    │ ESP32 receives 200 OK
    ▼
ESP32 returns to Deep Sleep
    │
    │ Sleep for 2 hours
    ▼
[Cycle repeats]
```

### Flow 2: Manual Trigger via Mobile App

```
User opens Mobile App
    │
    │ Clicks "Check Mailbox" button
    ▼
App checks user subscription
    │
    │ Free user: Check click count (< 3 today?)
    │ Premium: Unlimited
    ▼
If allowed:
    POST /api/device/trigger/
    {
      "device_serial": "ESP-12345",
      "user_id": 123
    }
    │
    │ Server validates
    ▼
Server checks device status
    │
    │ Device in deep sleep?
    ▼
Server sends wake command (if cellular) OR
Server queues request (device will check on next wake)
    │
    │ ESP32 wakes (if cellular) or on next timer
    ▼
ESP32 captures photo
    │
    │ Uploads to server
    ▼
[Same flow as automatic capture]
    │
    │ AI analysis
    ▼
Push notification sent
    │
    │ User sees result
    ▼
App updates click count (free users)
    │
    │ If 3 clicks used, disable button
    ▼
[Complete]
```

### Flow 3: ChatGPT Vision API Integration

```
Server receives photo
    │
    │ Store in database
    ▼
Create analysis task
    │
    │ Queue for processing
    ▼
Call ChatGPT Vision API
    POST https://api.openai.com/v1/chat/completions
    {
      "model": "gpt-4-vision-preview",
      "messages": [{
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Analyze this mailbox image. Determine if there is mail 
                     (letters, packages, envelopes) present. Respond with 
                     JSON: {\"mail_detected\": true/false, \"confidence\": 0.0-1.0, 
                     \"description\": \"brief description\"}"
          },
          {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,..."}
          }
        ]
      }]
    }
    │
    │ API processes
    ▼
Receive response
    {
      "mail_detected": true,
      "confidence": 0.92,
      "description": "Mailbox contains 2 envelopes visible"
    }
    │
    │ Store result
    ▼
Update Capture record
    │
    │ Trigger notification
    ▼
Send push notification
    │
    │ User receives
    ▼
[Complete]
```

## Component Details

### ESP32-CAM Device

**Hardware:**
- ESP32 microcontroller
- OV2640 camera (2MP)
- WiFi connectivity (or cellular via A7670)
- Deep sleep capability

**Firmware Behavior:**
- Wakes every 2 hours (7200 seconds)
- Can wake on manual trigger (if cellular enabled)
- Captures single photo per wake
- Uploads via WiFi or cellular
- Returns to deep sleep immediately after upload

**Power States:**
- **Deep Sleep**: ~10µA @ 3.3V = 0.033mW
- **Active (WiFi connecting)**: ~80mA @ 3.3V = 264mW
- **Active (WiFi connected)**: ~200mA @ 3.3V = 660mW
- **Active (camera capture)**: ~240mA @ 3.3V = 792mW
- **Active (uploading)**: ~200mA @ 3.3V = 660mW

### Cloud Server (Django)

**API Endpoints:**

1. **POST /api/device/capture/**
   - Receives photo from ESP32
   - Stores in database
   - Queues for AI analysis
   - Returns capture_id

2. **POST /api/device/trigger/**
   - Manual trigger request from app
   - Validates user permissions
   - Checks click limits (free users)
   - Sends wake command or queues request
   - Returns trigger_id

3. **GET /api/device/status/**
   - Returns device status
   - Last capture time
   - Battery level
   - Connection status

**Database Models:**
- Device (serial, user, status)
- Capture (device, image, timestamp, trigger_type)
- CaptureAnalysis (capture, mail_detected, confidence, description)
- User (email, subscription_tier)
- ClickLimit (user, date, count)

### ChatGPT Vision API

**Integration:**
- Uses GPT-4 Vision model
- Sends base64-encoded image
- Receives JSON response with mail detection
- Handles rate limits and errors
- Caches results for duplicate images

**Prompt:**
```
Analyze this mailbox image. Determine if there is mail 
(letters, packages, envelopes) present. Respond with JSON:
{
  "mail_detected": true/false,
  "confidence": 0.0-1.0,
  "description": "brief description"
}
```

### Mobile App

**Features:**
- Device registration
- Manual trigger button
- View capture history
- Push notifications
- Subscription management

**User Tiers:**
- **Free**: 3 manual clicks per day
- **Premium**: Unlimited manual clicks

**Click Limit Logic:**
- Track clicks per user per day
- Reset at midnight (user's timezone)
- Disable button when limit reached
- Show countdown to reset

## Data Flow Summary

| Step | Component | Action | Duration |
|------|-----------|--------|----------|
| 1 | ESP32 | Wake from sleep | 2-3s |
| 2 | ESP32 | Connect WiFi | 5-10s |
| 3 | ESP32 | Capture photo | 1-2s |
| 4 | ESP32 | Upload to server | 3-5s |
| 5 | Server | Store in DB | <1s |
| 6 | Server | Call ChatGPT API | 2-5s |
| 7 | Server | Process response | <1s |
| 8 | Server | Send notification | <1s |
| 9 | ESP32 | Return to sleep | <1s |
| **Total** | | | **~15-25s** |

## Error Handling

### ESP32 Errors
- WiFi connection failure → Retry 3 times, then sleep
- Photo capture failure → Skip this cycle, sleep
- Upload failure → Retry 3 times, then sleep
- Low battery → Send warning, continue operation

### Server Errors
- ChatGPT API failure → Retry with exponential backoff
- Database error → Log and notify admin
- Notification failure → Queue for retry

### User Errors
- Click limit exceeded → Return error, don't trigger
- Device offline → Queue request, notify user
- Invalid device → Return 404 error

## Security Considerations

1. **Device Authentication**: Serial number validation
2. **API Security**: Rate limiting, authentication tokens
3. **Image Storage**: Encrypted at rest
4. **User Data**: GDPR compliant, encrypted
5. **API Keys**: Secure storage, rotation policy

## Scalability

- **Horizontal Scaling**: Multiple server instances
- **Queue System**: Redis for job queuing
- **Database**: PostgreSQL with read replicas
- **CDN**: Image storage on S3/CloudFront
- **Caching**: Redis for frequently accessed data


