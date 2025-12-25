# Check Mailbox Button - Implementation Guide

## Overview

A "Check Mailbox" button has been added to the dashboard that allows users to manually trigger a photo capture from their ESP32-CAM device. The button includes click limit tracking for free users (3 clicks per day) and unlimited clicks for premium users.

## Features

### ✅ Manual Trigger Button
- **Location**: Dashboard, in the "Recent Mail" section
- **Function**: Triggers ESP32 to capture photo on next wake cycle
- **Visibility**: Only shows if user has at least one device

### ✅ Click Limit Display
- **Free Users**: Shows "X/3 clicks used today"
- **Premium Users**: No limit display (unlimited)
- **Auto-updates**: Refreshes every minute

### ✅ Result Display
- **Success Modal**: Shows confirmation when trigger is queued
- **Error Modal**: Shows error if limit exceeded or device offline
- **Auto-refresh**: Page reloads after modal closes to show new captures

## How It Works

### User Flow

1. **User clicks "Check Mailbox" button**
   - Button checks if user can click (limit not exceeded)
   - Shows loading state: "⏳ Checking..."

2. **API Request**
   - Sends POST to `/api/device/trigger/`
   - Includes device serial number
   - Validates click limits

3. **Server Response**
   - **Success (202)**: "Device will capture photo on next wake cycle"
   - **Error (429)**: "Daily limit reached"
   - **Error (404)**: "No device found"

4. **Result Display**
   - Success/Error modal appears
   - Click count updates
   - Page auto-refreshes to show new capture

5. **ESP32 Action**
   - Device wakes on next 2-hour cycle
   - Captures photo
   - Uploads to server
   - ChatGPT analyzes image
   - User receives notification

## API Endpoints

### POST /api/device/trigger/
**Purpose**: Manual trigger request

**Request:**
```json
{
  "device_serial": "ESP-12345"  // Optional, uses first device if not provided
}
```

**Response (Success):**
```json
{
  "status": "queued",
  "message": "Device will capture photo on next wake cycle (within 2 hours)",
  "device_serial": "ESP-12345"
}
```

**Response (Limit Exceeded):**
```json
{
  "status": "error",
  "error": "click_limit_exceeded",
  "message": "You have reached your daily limit of 3 manual clicks",
  "clicks_used": 3,
  "clicks_limit": 3,
  "reset_at": "2024-01-02T00:00:00Z"
}
```

### GET /api/device/click-status/
**Purpose**: Get click limit status

**Response:**
```json
{
  "has_device": true,
  "device_serial": "ESP-12345",
  "clicks_used_today": 2,
  "clicks_limit": 3,
  "clicks_remaining": 1,
  "user_tier": "free",
  "can_click": true,
  "reset_at": "2024-01-02T00:00:00Z"
}
```

## Click Limit Logic

### Free Users
- **Limit**: 3 manual clicks per day
- **Reset**: Midnight (user's timezone)
- **Tracking**: Counts captures with `motion_detected=False` (manual triggers)
- **Display**: Shows "X/3 clicks used today"

### Premium Users
- **Limit**: Unlimited
- **Tracking**: No limit checking
- **Display**: No click counter shown

## Button States

### Enabled State
- Blue background: `bg-blue-600`
- Text: "📬 Check Mailbox"
- Clickable: Yes

### Disabled State (Limit Reached)
- Gray background: `bg-gray-400`
- Text: "📬 Check Mailbox"
- Clickable: No (shows error modal if clicked)

### Loading State
- Blue background: `bg-blue-600`
- Text: "⏳ Checking..."
- Clickable: No

## User Experience

### When User Has Devices
- Button appears in "Recent Mail" section header
- Click limit displayed next to button (free users)
- Button enabled/disabled based on limit

### When No Mail Yet
- Button appears in empty state area
- Same functionality as header button
- Click limit displayed below button

### After Clicking
1. Button shows "⏳ Checking..."
2. Modal appears with result
3. Click count updates
4. Page refreshes to show new capture (if available)

## Integration with ESP32

### Current Implementation
- Manual trigger is **queued** (not immediate)
- ESP32 will capture on next 2-hour wake cycle
- User receives notification when photo is ready

### Future Enhancement
- Can add cellular wake functionality for immediate capture
- Would require A7670 module and wake signal

## Testing

### Test Scenarios

1. **Free User - First Click**
   - Click button
   - Should succeed
   - Counter shows "1/3"

2. **Free User - Limit Reached**
   - Click 3 times
   - 4th click should show error
   - Counter shows "3/3"

3. **Premium User**
   - Unlimited clicks
   - No counter displayed
   - All clicks succeed

4. **No Device**
   - Button disabled
   - Shows "Add device first" message

5. **Device Offline**
   - Trigger queued
   - Device captures on next wake
   - User notified when ready

## Files Modified

1. **django-webapp/devices/api_views.py**
   - Added `manual_trigger()` endpoint
   - Added `click_status()` endpoint
   - Updated `capture_upload()` to handle `trigger_type`

2. **django-webapp/devices/urls.py**
   - Added `/api/device/trigger/` route
   - Added `/api/device/click-status/` route

3. **django-webapp/web/templates/web/dashboard.html**
   - Added "Check Mailbox" button
   - Added click limit display
   - Added JavaScript for button functionality
   - Added result modal

## Next Steps

1. **Test the button** in the web interface
2. **Verify click limits** work correctly
3. **Test with ESP32** - ensure captures are marked as manual
4. **Monitor notifications** - ensure users receive results

## Notes

- Manual triggers are identified by `motion_detected=False` in Capture model
- Click limits reset at midnight (server timezone)
- Premium users bypass all limits
- Button automatically refreshes click status every minute


