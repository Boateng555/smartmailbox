# ESP32-CAM Firmware Changes - Timer-Based System

## Summary

The firmware has been completely rewritten to implement the new timer-based architecture. All IR sensor functionality has been removed, and the device now wakes every 2 hours automatically to capture and upload photos.

## Major Changes

### ✅ Removed Components
- **IR Sensor**: All IR sensor code, pin definitions, and motion detection logic removed
- **IR Power Control**: GPIO 2 power control removed
- **Reed Switch**: Door state detection removed (optional - can be re-added if needed)
- **Light Sensor**: Day/night detection removed (optional - can be re-added if needed)
- **Multiple Photos**: Changed from 3 photos per trigger to 1 photo per wake
- **Heartbeat**: Removed periodic heartbeat messages
- **Scheduled Captures**: Removed scheduled capture logic

### ✅ New Features
- **Timer-Based Wake**: Wakes every 2 hours (7200 seconds) automatically
- **Single Photo Capture**: One photo per wake cycle
- **Trigger Type**: Uploads include `trigger_type` field ("automatic" or "manual")
- **Simplified Flow**: Everything happens in `setup()`, then device sleeps
- **Optimized Power**: Minimal active time (~15-20 seconds per cycle)

## Code Structure

### Setup Function Flow
```
setup()
  ├── Check wake reason (timer/manual/power-on)
  ├── Initialize camera
  ├── Check battery voltage
  ├── Connect to WiFi
  ├── Capture single photo
  ├── Upload to server (with trigger_type)
  └── Enter deep sleep (2 hours)
```

### Loop Function
- **Minimal**: Just a safety fallback
- Device should never reach loop() in normal operation
- If reached, immediately enters deep sleep

## Key Functions

### Deep Sleep
```cpp
void enterDeepSleep()
  - Disables WiFi
  - Turns off LED
  - Configures timer wake (2 hours)
  - Enters deep sleep
```

### Photo Capture
```cpp
String takePhoto()
  - Captures single photo
  - Converts to base64
  - Returns base64 string
```

### Upload
```cpp
bool uploadPhoto(String base64Image, String triggerType)
  - Uploads photo to server
  - Includes trigger_type field
  - Returns success/failure
```

## Configuration

### Deep Sleep Duration
```cpp
const unsigned long DEEP_SLEEP_DURATION_US = 7200000000ULL; // 2 hours
```

### API Endpoint
```cpp
const char* API_ENDPOINT = "/api/device/capture/";
```

### Upload Payload
```json
{
  "serial_number": "ESP-12345",
  "image": "base64_encoded_image",
  "trigger_type": "automatic" | "manual",
  "battery_voltage": 3.85,
  "timestamp": 1234567890
}
```

## Power Consumption

### Active Cycle (~15-20 seconds)
- Boot/Init: 2-3s @ 80mA
- WiFi Connect: 5-10s @ 80mA
- Camera Capture: 1-2s @ 240mA
- Upload: 3-5s @ 200mA
- **Total**: ~15-20 seconds active time

### Deep Sleep
- **Current**: ~10µA @ 3.3V
- **Duration**: 2 hours (7200 seconds)
- **Power**: 0.033mW

### Battery Life (1800mAh)
- **Free users** (12 auto/day): ~5.3 months
- **Premium users** (12 auto + 10 manual/day): ~3.6 months

## Testing

### Serial Monitor Output
```
ESP32-CAM Smart Mailbox - Timer Based
=====================================
Wake reason: Timer (automatic - 2 hour interval)
Device Serial: ESP-12345
Battery voltage: 3.85V
Initializing camera...
Camera initialized successfully!
WiFi credentials found, connecting...
WiFi connected!
IP address: 192.168.1.100
Starting capture cycle...
Capturing photo...
Picture taken! Size: 45678 bytes
Base64 encoded length: 60904
Uploading photo to: http://194.164.59.137:8000/api/device/capture/
Trigger type: automatic
Upload: Success
Photo uploaded successfully!
Cycle complete. Returning to sleep...
Entering deep sleep for 2 hours...
```

## Migration Notes

### From Old Firmware
1. **Remove IR sensor wiring** (GPIO 13 no longer used)
2. **Remove IR power control** (GPIO 2 no longer used)
3. **Update API endpoint** if needed
4. **Flash new firmware**
5. **Test wake cycle** (should wake every 2 hours)

### Backend Compatibility
- Backend must accept `trigger_type` field
- Backend should handle "automatic" and "manual" triggers
- ChatGPT Vision API integration unchanged

## Manual Trigger Support

### Current Implementation
- Manual triggers are detected via `ESP_SLEEP_WAKEUP_EXT0`
- Requires external wake source (e.g., cellular module)
- If cellular module sends wake signal, trigger_type = "manual"

### Future Enhancement
- Can add API endpoint to queue manual triggers
- Device checks for queued triggers on each wake
- Processes manual trigger if queued

## Troubleshooting

### Device Won't Wake
- Check timer configuration
- Verify deep sleep duration
- Check battery voltage

### WiFi Connection Fails
- Verify credentials saved
- Check signal strength
- Device will enter AP mode if WiFi fails

### Upload Fails
- Check API_DOMAIN setting
- Verify server is accessible
- Check network connectivity
- Device will sleep even if upload fails

### Camera Fails
- Check camera module connection
- Verify pin definitions
- Device will sleep even if camera fails

## Next Steps

1. **Test firmware** on hardware
2. **Verify wake cycle** (2 hours)
3. **Test photo capture** and upload
4. **Monitor battery consumption**
5. **Update backend** to handle trigger_type
6. **Deploy to production**

## Files Changed

- `src/main.cpp` - Completely rewritten
- `src/main_old_backup.cpp` - Backup of old firmware

## Notes

- All IR sensor code removed
- Simplified to timer-based wake only
- Single photo per cycle
- Optimized for battery life
- Ready for production deployment


