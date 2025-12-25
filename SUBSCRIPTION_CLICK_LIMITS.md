# Subscription Click Limits

## Click Limit Configuration

### Free Users
- **Daily Limit**: 3 manual clicks per day
- **Reset**: Midnight (server timezone)
- **Display**: Shows "X/3 clicks today"

### Premium Users
- **Daily Limit**: 10 manual clicks per day
- **Reset**: Midnight (server timezone)
- **Display**: Shows "X/10 clicks today"

## Implementation

### API Endpoints

**POST /api/device/trigger/**
- Checks click limit before allowing trigger
- Free: 3 clicks/day
- Premium: 10 clicks/day

**GET /api/device/click-status/**
- Returns current click status
- Shows clicks used and limit for both tiers

### Response Format

```json
{
  "has_device": true,
  "device_serial": "ESP-12345",
  "clicks_used_today": 2,
  "clicks_limit": 10,  // 3 for free, 10 for premium
  "clicks_remaining": 8,
  "user_tier": "premium",  // or "free"
  "can_click": true,
  "reset_at": "2024-01-02T00:00:00Z"
}
```

## User Experience

### Free Users
- See "X/3 clicks today" counter
- Button disables after 3 clicks
- Error message: "You have reached your daily limit of 3 manual clicks"

### Premium Users
- See "X/10 clicks today" counter
- Button disables after 10 clicks
- Error message: "You have reached your daily limit of 10 manual clicks"

## Files Updated

1. **django-webapp/devices/api_views.py**
   - `manual_trigger()`: Checks 3 clicks for free, 10 for premium
   - `click_status()`: Returns correct limit based on tier

2. **django-webapp/web/templates/web/dashboard.html**
   - Click limit display shows for both tiers
   - Updates dynamically based on user subscription

## Testing

### Test Free User
1. Create free user account
2. Click "Check Mailbox" 3 times
3. 4th click should show error: "Daily limit of 3 clicks"

### Test Premium User
1. Create premium subscription
2. Click "Check Mailbox" 10 times
3. 11th click should show error: "Daily limit of 10 clicks"

## Summary

✅ **Free Users**: 3 clicks per day
✅ **Premium Users**: 10 clicks per day
✅ **Counter Display**: Shows for both tiers
✅ **Auto-Reset**: At midnight daily


