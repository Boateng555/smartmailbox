# Complete App Architecture Update

## Overview
The entire Django app has been updated to match the new timer-based architecture, removing all IR sensor and motion detection features.

## Major Changes

### 1. Models Updated

#### Device Model (`devices/models.py`)
- ❌ **Removed**: `ir_sensor_status` field
- ❌ **Removed**: `last_motion_time` field
- ❌ **Removed**: `IR_SENSOR_STATUS_CHOICES`
- ❌ **Removed**: `reset_motion_status_if_expired()` method
- ✅ **Kept**: All other fields (power_state, connection_type, etc.)

#### Capture Model (`devices/models.py`)
- ❌ **Removed**: `motion_detected` boolean field
- ✅ **Added**: `trigger_type` field with choices:
  - `'automatic'` - Timer-based (every 2 hours)
  - `'manual'` - User-initiated via app button
- ✅ **Kept**: All other fields (door_open, battery_voltage, solar_charging)

### 2. API Endpoints Updated

#### `POST /api/device/capture/` (`devices/api_views.py`)
- ✅ Now accepts `trigger_type` instead of `motion_detected`
- ✅ Defaults to `'automatic'` if not provided
- ✅ WebSocket messages updated to use `trigger_type`

#### `POST /api/device/trigger/` (`devices/api_views.py`)
- ✅ Manual trigger endpoint
- ✅ Checks click limits: Free (3/day), Premium (10/day)
- ✅ Returns 202 Accepted when queued

#### `GET /api/device/click-status/` (`devices/api_views.py`)
- ✅ Returns click limit status
- ✅ Shows clicks used/limit based on subscription tier

### 3. Admin Interface Updated

#### DeviceAdmin (`devices/admin.py`)
- ❌ **Removed**: `ir_sensor_status` from list_display
- ❌ **Removed**: `last_motion_time` from list_display
- ❌ **Removed**: `ir_sensor_status` from list_filter
- ✅ **Added**: `power_state` to list_display and list_filter

#### CaptureAdmin (`devices/admin.py`)
- ❌ **Removed**: `motion_detected` from list_display
- ❌ **Removed**: `motion_detected` from list_filter
- ✅ **Added**: `trigger_type` to list_display and list_filter

### 4. WebSocket Consumers Updated

#### DeviceFeedConsumer (`web/consumers.py`)
- ❌ **Removed**: `motion_detected` from WebSocket messages
- ❌ **Removed**: `ir_sensor_status` from WebSocket messages
- ✅ **Added**: `trigger_type` to WebSocket messages

### 5. Subscription Click Limits

#### Free Users
- **Limit**: 3 manual clicks per day
- **Reset**: Midnight daily
- **Display**: "X/3 clicks today"

#### Premium Users
- **Limit**: 10 manual clicks per day
- **Reset**: Midnight daily
- **Display**: "X/10 clicks today"

### 6. Templates to Update

The following templates still need updates (motion detection references):
- `web/templates/web/device_detail.html` - Remove motion badges and notifications
- `web/templates/web/admin/support.html` - Remove motion detection section
- `web/templates/web/admin/diagnostics.html` - Remove IR sensor status
- `web/templates/web/debug.html` - Update motion column

### 7. Old Views to Remove/Update

#### `devices/views.py`
- ❌ **Remove**: `device_capture()` function (old endpoint with IR sensor logic)
- ✅ **Keep**: `device_heartbeat()` function

### 8. Serializers to Update

#### `devices/serializers.py`
- ❌ **Remove**: `motion_detected` field from DeviceCaptureSerializer
- ❌ **Remove**: `ir_sensor_status` and `last_motion_time` from DeviceSerializer

## Migration Steps

1. **Create Migration**:
   ```bash
   python manage.py makemigrations devices
   ```

2. **Review Migration**:
   - Check `devices/migrations/0007_remove_ir_sensor_add_trigger_type.py`

3. **Run Migration**:
   ```bash
   python manage.py migrate
   ```

4. **Update Data** (if needed):
   - Convert existing `motion_detected=True` captures to `trigger_type='automatic'`
   - Convert existing `motion_detected=False` captures to `trigger_type='manual'`

## Testing Checklist

- [ ] Device model no longer has IR sensor fields
- [ ] Capture model uses trigger_type instead of motion_detected
- [ ] API accepts trigger_type parameter
- [ ] WebSocket messages include trigger_type
- [ ] Admin interface shows trigger_type
- [ ] Click limits work: Free (3), Premium (10)
- [ ] Manual trigger button works
- [ ] Automatic captures marked as 'automatic'
- [ ] Manual captures marked as 'manual'

## Files Modified

1. ✅ `devices/models.py` - Updated Device and Capture models
2. ✅ `devices/api_views.py` - Updated capture_upload, manual_trigger, click_status
3. ✅ `devices/admin.py` - Updated admin interfaces
4. ✅ `web/consumers.py` - Updated WebSocket consumer
5. ⏳ `web/templates/web/device_detail.html` - Needs motion removal
6. ⏳ `web/templates/web/admin/support.html` - Needs motion removal
7. ⏳ `devices/views.py` - Needs old device_capture removal
8. ⏳ `devices/serializers.py` - Needs motion field removal

## Next Steps

1. Complete template updates
2. Remove old views
3. Update serializers
4. Run migrations
5. Test all functionality
6. Update documentation


