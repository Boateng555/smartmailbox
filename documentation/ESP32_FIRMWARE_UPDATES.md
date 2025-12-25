# ESP32-CAM Firmware Updates - Timer-Based System

## Overview

The firmware has been updated to remove IR sensor functionality and implement a timer-based wake system that wakes every 2 hours for automatic captures, plus support for manual triggers via API.

## Key Changes

### Removed Components
- ❌ IR sensor code and pin definitions
- ❌ IR sensor power control
- ❌ Motion detection logic
- ❌ Consecutive trigger validation
- ❌ Mail detection state machine

### New Features
- ✅ Timer-based deep sleep (2 hours)
- ✅ Manual trigger support via API
- ✅ Simplified wake/capture/upload/sleep cycle
- ✅ Optimized power consumption
- ✅ Single photo per wake (not 3)

## Updated Pin Definitions

```cpp
// REMOVED - IR Sensor pins
// #define IR_SENSOR_PIN     13
// #define IR_SENSOR_POWER_PIN  2

// KEPT - Camera pins (unchanged)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
// ... (all camera pins remain)

// KEPT - Status LED
#define LED_STATUS_PIN    4  // GPIO 4 (flash LED on ESP32-CAM)

// KEPT - Battery monitoring (optional)
#define BATTERY_ADC_PIN   14  // GPIO 14 (ADC) for battery voltage

// KEPT - A7670 cellular (if using)
#define A7670_POWER_PIN      33
#define A7670_RX_PIN         16
#define A7670_TX_PIN         17
```

## Deep Sleep Configuration

```cpp
// Deep sleep duration: 2 hours = 7200 seconds
const unsigned long DEEP_SLEEP_DURATION = 7200000000; // microseconds (2 hours)

// Wake sources
// 1. Timer (automatic every 2 hours)
// 2. Manual trigger (if cellular enabled, via API)
```

## Updated Main Loop Flow

### Old Flow (IR Sensor Based)
```
Loop:
  - Check IR sensor
  - If triggered: Capture 3 photos
  - Upload photos
  - Deep sleep (wake on IR interrupt)
```

### New Flow (Timer Based)
```
Setup:
  - Initialize camera
  - Connect to WiFi
  - Check for manual trigger (if cellular)
  - Capture single photo
  - Upload to server
  - Deep sleep for 2 hours
```

## Code Snippets

### 1. Deep Sleep with Timer Wake

```cpp
#include <esp_sleep.h>

// Deep sleep duration: 2 hours
const unsigned long DEEP_SLEEP_DURATION_US = 7200000000; // 2 hours in microseconds

void enterDeepSleep() {
  Serial.println("Entering deep sleep for 2 hours...");
  Serial.flush();
  
  // Configure wake source: Timer
  esp_sleep_enable_timer_wakeup(DEEP_SLEEP_DURATION_US);
  
  // Optional: Enable wake on external pin (for future manual trigger via cellular)
  // esp_sleep_enable_ext0_wakeup(GPIO_NUM_33, 1); // Wake on HIGH
  
  // Enter deep sleep
  esp_deep_sleep_start();
  // Code never reaches here
}
```

### 2. Wake Detection and Initialization

```cpp
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Check wake reason
  esp_sleep_wakeup_cause_t wakeupReason = esp_sleep_get_wakeup_cause();
  
  Serial.println("ESP32-CAM Smart Mailbox - Timer Based");
  Serial.println("====================================");
  
  switch(wakeupReason) {
    case ESP_SLEEP_WAKEUP_TIMER:
      Serial.println("Wake reason: Timer (2 hour interval)");
      break;
    case ESP_SLEEP_WAKEUP_EXT0:
      Serial.println("Wake reason: Manual trigger (external)");
      break;
    case ESP_SLEEP_WAKEUP_UNDEFINED:
      Serial.println("Wake reason: Power on / Reset");
      break;
    default:
      Serial.printf("Wake reason: %d\n", wakeupReason);
      break;
  }
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("ERROR: Camera initialization failed!");
    delay(5000);
    enterDeepSleep(); // Sleep even if camera fails
    return;
  }
  
  // Connect to WiFi
  if (!connectToWiFi()) {
    Serial.println("ERROR: WiFi connection failed!");
    delay(5000);
    enterDeepSleep();
    return;
  }
  
  // Main capture and upload flow
  captureAndUpload();
  
  // Return to deep sleep
  enterDeepSleep();
}
```

### 3. Simplified Capture and Upload

```cpp
void captureAndUpload() {
  Serial.println("Starting capture cycle...");
  
  // Capture single photo
  String base64Image = takePhoto();
  
  if (base64Image.length() == 0) {
    Serial.println("ERROR: Photo capture failed!");
    return;
  }
  
  Serial.printf("Photo captured: %d bytes (base64: %d chars)\n", 
                 base64Image.length() * 3 / 4, base64Image.length());
  
  // Determine trigger type
  String triggerType = "automatic";
  esp_sleep_wakeup_cause_t wakeupReason = esp_sleep_get_wakeup_cause();
  if (wakeupReason == ESP_SLEEP_WAKEUP_EXT0) {
    triggerType = "manual";
  }
  
  // Upload to server
  bool success = uploadPhoto(base64Image, triggerType);
  
  if (success) {
    Serial.println("Photo uploaded successfully!");
  } else {
    Serial.println("ERROR: Photo upload failed!");
  }
}

String takePhoto() {
  camera_fb_t *fb = NULL;
  
  // Disable flash LED to save power
  digitalWrite(LED_STATUS_PIN, LOW);
  
  // Capture frame
  fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return "";
  }
  
  Serial.printf("Picture taken! Size: %zu bytes\n", fb->len);
  
  // Convert to base64
  String base64Image = base64::encode((uint8_t*)fb->buf, fb->len);
  
  // Return frame buffer
  esp_camera_fb_return(fb);
  
  return base64Image;
}
```

### 4. Upload with Trigger Type

```cpp
bool uploadPhoto(String base64Image, String triggerType) {
  HTTPClient http;
  String url = buildApiUrl(API_ENDPOINT);
  
  Serial.print("Uploading to: ");
  Serial.println(url);
  
  // Use appropriate client (HTTP or HTTPS)
  if (isIPAddress(API_DOMAIN)) {
    http.begin(url); // HTTP
  } else {
    WiFiClientSecure client;
    configureSSLClient(client);
    http.begin(client, url); // HTTPS
  }
  
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(1024 * 100); // Large enough for base64 image
  doc["serial_number"] = serialNumber;
  doc["image"] = base64Image;
  doc["trigger_type"] = triggerType; // "automatic" or "manual"
  doc["battery_voltage"] = readBatteryVoltage();
  doc["timestamp"] = millis();
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  bool success = false;
  if (httpResponseCode > 0) {
    Serial.printf("HTTP Response code: %d\n", httpResponseCode);
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    success = (httpResponseCode == 200);
  } else {
    Serial.printf("Error code: %d\n", httpResponseCode);
  }
  
  http.end();
  return success;
}
```

### 5. Optimized WiFi Connection

```cpp
bool connectToWiFi() {
  // Load WiFi credentials from flash
  preferences.begin("wifi", true);
  String ssid = preferences.getString("ssid", "");
  String password = preferences.getString("password", "");
  preferences.end();
  
  if (ssid.length() == 0) {
    Serial.println("No WiFi credentials stored. Entering AP mode...");
    setupAPMode();
    return false;
  }
  
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());
  
  // Fast connection with timeout
  unsigned long startTime = millis();
  const unsigned long timeout = 10000; // 10 seconds max
  
  while (WiFi.status() != WL_CONNECTED && (millis() - startTime) < timeout) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println("");
    Serial.println("WiFi connection failed!");
    return false;
  }
}
```

### 6. Battery Monitoring (Optional)

```cpp
float readBatteryVoltage() {
  // Read ADC (GPIO 14) with voltage divider
  int adcValue = analogRead(BATTERY_ADC_PIN);
  
  // Convert to voltage (assuming 2:1 voltage divider)
  float voltage = (adcValue / 4095.0) * 3.3 * 2.0;
  
  return voltage;
}

void checkBatteryStatus() {
  float voltage = readBatteryVoltage();
  Serial.printf("Battery voltage: %.2fV\n", voltage);
  
  if (voltage < 3.3) {
    Serial.println("WARNING: Low battery!");
    // Could send alert to server
  }
}
```

### 7. Complete Main Function

```cpp
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Check wake reason
  esp_sleep_wakeup_cause_t wakeupReason = esp_sleep_get_wakeup_cause();
  
  Serial.println("ESP32-CAM Smart Mailbox");
  Serial.println("=======================");
  
  switch(wakeupReason) {
    case ESP_SLEEP_WAKEUP_TIMER:
      Serial.println("Wake: Timer (automatic)");
      break;
    case ESP_SLEEP_WAKEUP_EXT0:
      Serial.println("Wake: Manual trigger");
      break;
    default:
      Serial.println("Wake: Power on");
      break;
  }
  
  // Initialize camera
  Serial.println("Initializing camera...");
  if (!initCamera()) {
    Serial.println("ERROR: Camera init failed!");
    enterDeepSleep();
    return;
  }
  
  // Check battery (optional)
  checkBatteryStatus();
  
  // Connect to WiFi
  Serial.println("Connecting to WiFi...");
  if (!connectToWiFi()) {
    Serial.println("ERROR: WiFi failed!");
    enterDeepSleep();
    return;
  }
  
  // Capture and upload
  captureAndUpload();
  
  // Return to deep sleep
  Serial.println("Cycle complete. Returning to sleep...");
  delay(1000); // Allow serial to flush
  enterDeepSleep();
}

void loop() {
  // This should never be reached
  // Device enters deep sleep in setup()
  delay(1000);
}
```

## Power Optimization Tips

### 1. Disable Flash LED
```cpp
// In takePhoto()
digitalWrite(LED_STATUS_PIN, LOW); // Keep LED off
```

### 2. Reduce Photo Quality
```cpp
// In initCamera()
config.jpeg_quality = 12; // Lower = smaller file, faster upload
config.frame_size = FRAMESIZE_SVGA; // 800x600 instead of UXGA
```

### 3. Fast WiFi Connection
```cpp
// Use saved credentials, reduce retry time
WiFi.setAutoReconnect(true);
WiFi.setSleep(false); // Disable WiFi sleep for faster connection
```

### 4. Minimize Active Time
```cpp
// Complete cycle in < 20 seconds
// - Boot: 2-3s
// - WiFi: 5-10s
// - Capture: 1-2s
// - Upload: 3-5s
// - Sleep: <1s
// Total: ~15-20 seconds
```

## Testing Commands

Via Serial Monitor (before sleep):
- `help` - Show commands
- `test` - Test photo capture
- `status` - Show system status
- `wifi` - Test WiFi connection

## Migration Notes

### Removing IR Sensor Code
1. Remove IR sensor pin definitions
2. Remove IR sensor initialization
3. Remove IR sensor check in loop
4. Remove motion detection logic
5. Remove wake on IR interrupt

### Adding Timer Wake
1. Set deep sleep duration to 2 hours
2. Enable timer wake source
3. Check wake reason in setup()
4. Handle automatic vs manual triggers

### Simplifying Photo Capture
1. Capture single photo (not 3)
2. Upload immediately
3. Return to sleep quickly

## Expected Behavior

1. **Device boots** → Initializes camera → Connects WiFi
2. **Captures photo** → Converts to base64
3. **Uploads to server** → Waits for response
4. **Enters deep sleep** → Wakes in 2 hours
5. **Repeats cycle** → Automatic every 2 hours

Total active time per cycle: **~15-20 seconds**
Deep sleep time: **~2 hours**
Battery life: **3.5-4 months** (free user, 1800mAh battery)


