#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <ESPAsyncWebServer.h>
#include <esp_ota_ops.h>
#include <esp_https_ota.h>
#include <HardwareSerial.h>
#include "esp_camera.h"
#include "Base64.h"

// ============================================================================
// CONFIGURATION SECTION - Update these for cloud server deployment
// ============================================================================
// 
// DEPLOYMENT INSTRUCTIONS:
// 1. Replace "YOUR_DOMAIN.com" below with your actual domain (e.g., "api.yourdomain.com")
//    - Do NOT include http:// or https:// - just the domain name
//    - Example: const char* API_DOMAIN = "api.smartcamera.com";
//
// 2. For SSL certificate validation (recommended for production):
//    - Get your CA certificate: openssl s_client -showcerts -connect YOUR_DOMAIN.com:443 </dev/null
//    - Set rootCACertificate to the certificate string
//    - Set validateSSL = true
//
// 3. Device serial number:
//    - Leave DEVICE_SERIAL empty to auto-generate from MAC address
//    - Or set a custom serial: const char* DEVICE_SERIAL = "ESP-TEST-001";
//
// ============================================================================

// Replace with your actual domain or IP address
// For IP address: Use the IP directly (e.g., "194.164.59.137")
// For domain: Use domain name (e.g., "api.yourdomain.com")
// Do NOT include http:// or https:// - just the domain/IP
const char* API_DOMAIN = "194.164.59.137";

// API endpoints (no leading slash needed, but it's fine if included)
const char* API_ENDPOINT = "/api/device/capture/";
const char* HEARTBEAT_ENDPOINT = "/api/device/heartbeat/";
const char* FIRMWARE_ENDPOINT = "/api/firmware/latest/";

// Device serial number - will be auto-generated from MAC if empty
// Format: "ESP-XXXXXX" (e.g., "ESP-TEST-001" or "ESP-123456")
const char* DEVICE_SERIAL = "";  // Leave empty to auto-generate from MAC address

// SSL/TLS Configuration
// Root CA certificate for certificate validation (set for production)
// To get your CA certificate, run: openssl s_client -showcerts -connect YOUR_DOMAIN.com:443 </dev/null
const char* rootCACertificate = NULL;  // Set to your CA certificate string for production
bool validateSSL = false;  // Set to true when CA certificate is configured

// Helper function to build API URL (HTTPS for domain, HTTP for IP)
String buildApiUrl(const char* endpoint) {
  String url;
  
  // Use HTTPS for domains, HTTP for IP addresses
  // Check if API_DOMAIN is an IP address (contains digits and dots, no letters)
  bool isIP = true;
  for (int i = 0; API_DOMAIN[i] != '\0'; i++) {
    char c = API_DOMAIN[i];
    if ((c < '0' || c > '9') && c != '.') {
      isIP = false;
      break;
    }
  }
  
  if (isIP) {
    url = "http://";  // Use HTTP for IP addresses (no SSL certificate)
  } else {
    url = "https://"; // Use HTTPS for domains
  }
  
  url += String(API_DOMAIN);
  
  // Add port if using IP (Django default is 8000)
  if (isIP) {
    url += ":8000";  // Add port for IP address
  }
  
  // Ensure endpoint starts with /
  if (endpoint[0] != '/') {
    url += "/";
  }
  url += endpoint;
  return url;
}

// Helper function to check if API_DOMAIN is an IP address
bool isIPAddress(const char* domain) {
  for (int i = 0; domain[i] != '\0'; i++) {
    char c = domain[i];
    if ((c < '0' || c > '9') && c != '.') {
      return false;
    }
  }
  return true;
}

// Helper function to configure SSL client with error handling
void configureSSLClient(WiFiClientSecure& client) {
  // Skip SSL for IP addresses (they don't have certificates)
  if (isIPAddress(API_DOMAIN)) {
    Serial.println("SSL: Skipped (using IP address with HTTP)");
    return;
  }
  
  if (validateSSL && rootCACertificate) {
    client.setCACert(rootCACertificate);
    Serial.println("SSL: Certificate validation enabled");
  } else {
    // Skip certificate validation (insecure, but allows connection)
    // WARNING: This is insecure and should only be used for testing
    // TODO: Configure proper CA certificate for production deployment
    client.setInsecure();
    Serial.println("SSL: WARNING - Certificate validation disabled (INSECURE)");
  }
  
  // Set timeout for SSL handshake
  client.setTimeout(10);
}
// ============================================================================

// Camera pin definitions for AI-Thinker board
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// IR Sensor pin for mail detection
#define IR_SENSOR_PIN     13
#define IR_SENSOR_POWER_PIN  2  // GPIO 2 for IR sensor power control (optional MOSFET)

// Light sensor pin for day/night detection (optional - LDR or photodiode)
#define LIGHT_SENSOR_PIN  14  // GPIO 14 (ADC) for light sensor

// Reed switch pin for door state detection
#define REED_SWITCH_PIN   12

// Battery monitoring pin (ADC for battery voltage)
#define BATTERY_ADC_PIN   14  // GPIO 14 (ADC2_CH6) for battery voltage monitoring

// Solar charging status pin (optional - can use GPIO 15)
#define SOLAR_CHARGE_PIN  15  // GPIO 15 for solar charging status

// LED Status pin (built-in LED on ESP32-CAM, or external LED)
#define LED_STATUS_PIN    4  // GPIO 4 (flash LED on ESP32-CAM)

// A7670 4G Module pins (cellular-first connectivity)
#define A7670_POWER_PIN      33  // GPIO 33 for power control (HIGH for 1s to boot) - Changed from GPIO 4 (conflict with LED)
#define A7670_RX_PIN         16  // UART RX (ESP32 receives from A7670)
#define A7670_TX_PIN         17  // UART TX (ESP32 sends to A7670)
#define A7670_BAUD           115200
#define A7670_UART_NUM       2   // Use UART2

// A7670 APN configuration (adjust per carrier)
const char* cellularAPN = "internet";  // Adjust per carrier
const char* cellularUser = "";         // Usually empty
const char* cellularPass = "";         // Usually empty

// WiFi fallback threshold (only use WiFi if signal > -70dBm)
#define WIFI_MIN_RSSI        -70

// Preferences for storing WiFi credentials
Preferences preferences;

// WiFi credentials (loaded from flash)
String wifiSSID = "";
String wifiPassword = "";


// Device serial number (last 3 chars of MAC)
String serialNumber = "";

// AP Mode
const char* apSSID = "SmartCamera-SETUP";
const char* apPassword = ""; // No password for easier setup
AsyncWebServer server(80);
bool apMode = false;

// Connection management
enum ConnectionType {
  CONN_NONE,
  CONN_WIFI,
  CONN_CELLULAR
};
ConnectionType currentConnection = CONN_NONE;
HardwareSerial a7670Serial(2); // Use UART2 for A7670
#include "a7670_cellular.h"
A7670Cellular cellular;

// WiFi failure tracking
unsigned long wifiFailureStartTime = 0;
const unsigned long wifiFailureTimeout = 300000; // 5 minutes in milliseconds
bool cellularEnabled = false;

// Timing
unsigned long lastHeartbeat = 0;
const unsigned long heartbeatInterval = 30000; // 30 seconds in milliseconds
unsigned long lastCapture = 0;
const unsigned long captureInterval = 60000; // 60 seconds in milliseconds
unsigned long lastFirmwareCheck = 0;
const unsigned long firmwareCheckInterval = 86400000; // 24 hours in milliseconds

// Firmware version
String currentFirmwareVersion = "1.0.0"; // Default version

// Debug tracking
unsigned long lastUploadTime = 0;
String serialInput = "";

// IR Sensor motion detection - optimized for mailbox
unsigned long lastMotionTrigger = 0;
const unsigned long motionDebounceInterval = 5000; // 5 seconds in milliseconds
bool motionDetected = false;

// False positive prevention - require 2 consecutive triggers
unsigned long firstTriggerTime = 0;
bool firstTriggerDetected = false;
const unsigned long CONSECUTIVE_TRIGGER_WINDOW = 5000; // 5 seconds window for 2 triggers
const unsigned long MAX_AWAKE_TIME = 30000; // 30 seconds max awake time
unsigned long wakeTime = 0;
bool isUploading = false; // Flag to ignore triggers during upload

// Light sensor for day/night detection
float lightLevel = 0.0;
const float LIGHT_THRESHOLD = 100.0; // ADC value threshold (adjust based on sensor)
bool isDaytime = true;

bool cameraInitialized = false;

// LED Status indicators
enum LEDStatus {
  LED_OFF,
  LED_WIFI_CONNECTING,    // Fast blink (100ms on/off)
  LED_WIFI_CONNECTED,      // Slow blink (500ms on/off)
  LED_ERROR,               // Rapid blink (50ms on/off)
  LED_MOTION,              // Double blink pattern
  LED_CAPTURING,           // Solid on
  LED_CELLULAR_ACTIVE      // Medium blink (200ms on/off)
};
LEDStatus currentLEDStatus = LED_OFF;
unsigned long lastLEDToggle = 0;
bool ledState = false;

// Deep sleep configuration for mailbox
bool deepSleepEnabled = true;
const unsigned long deepSleepDuration = 3600000; // 1 hour in milliseconds (default wake-up timer)
unsigned long lastActivityTime = 0;
bool wokeFromDeepSleep = false;
esp_sleep_wakeup_cause_t wakeupReason;

// Mailbox state
bool doorOpen = false;
bool mailDetected = false;
unsigned long lastDoorStateChange = 0;
const unsigned long doorDebounceInterval = 100; // 100ms debounce for reed switch


// Battery and power management
float batteryVoltage = 0.0;
bool solarCharging = false;
const float BATTERY_MIN_VOLTAGE = 3.0;  // Minimum safe voltage (V)
const float BATTERY_MAX_VOLTAGE = 4.2;  // Maximum voltage (V)
const float BATTERY_LOW_THRESHOLD = 3.3; // Low battery threshold (V)
const int BATTERY_ADC_RESOLUTION = 12;   // 12-bit ADC (0-4095)
const float ADC_REF_VOLTAGE = 3.3;      // Reference voltage
const float VOLTAGE_DIVIDER_RATIO = 2.0; // Voltage divider ratio (if using divider)

// Photo capture settings
const int PHOTOS_PER_TRIGGER = 3;        // Take 3 photos when IR triggers
const unsigned long PHOTO_INTERVAL = 2000; // 2 seconds between photos

// Watchdog timer
hw_timer_t *watchdogTimer = NULL;
const unsigned long watchdogTimeout = 60000; // 60 seconds
unsigned long lastWatchdogFeed = 0;

// Generate device serial from MAC address or use configured serial
String getDeviceSerial() {
  // Use configured serial if provided
  if (strlen(DEVICE_SERIAL) > 0) {
    return String(DEVICE_SERIAL);
  }
  
  // Otherwise generate from MAC address
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  char serial[10];
  sprintf(serial, "ESP-%02X%02X%02X", mac[3], mac[4], mac[5]);
  return String(serial);
}

// LED Status indicator functions
void setLEDStatus(LEDStatus status) {
  currentLEDStatus = status;
  lastLEDToggle = millis();
  ledState = false;
  digitalWrite(LED_STATUS_PIN, LOW);
}

void updateLED() {
  unsigned long currentTime = millis();
  unsigned long interval = 0;
  bool shouldBlink = false;
  
  switch (currentLEDStatus) {
    case LED_OFF:
      digitalWrite(LED_STATUS_PIN, LOW);
      return;
      
    case LED_WIFI_CONNECTING:
      interval = 100;
      shouldBlink = true;
      break;
      
    case LED_WIFI_CONNECTED:
      interval = 500;
      shouldBlink = true;
      break;
      
    case LED_ERROR:
      interval = 50;
      shouldBlink = true;
      break;
      
    case LED_MOTION:
      // Double blink pattern: blink-blink-pause
      if ((currentTime - lastLEDToggle) % 600 < 100 || 
          (currentTime - lastLEDToggle) % 600 < 200) {
        shouldBlink = true;
      }
      interval = 100;
      break;
      
    case LED_CAPTURING:
      digitalWrite(LED_STATUS_PIN, HIGH);
      return;
      
    case LED_CELLULAR_ACTIVE:
      interval = 200;
      shouldBlink = true;
      break;
  }
  
  if (shouldBlink && (currentTime - lastLEDToggle >= interval)) {
    ledState = !ledState;
    digitalWrite(LED_STATUS_PIN, ledState ? HIGH : LOW);
    lastLEDToggle = currentTime;
  }
}

// Watchdog timer interrupt handler
void IRAM_ATTR watchdogInterrupt() {
  Serial.println("Watchdog timer expired! System frozen, rebooting...");
  ESP.restart();
}

void initWatchdog() {
  watchdogTimer = timerBegin(0, 80, true); // Timer 0, prescaler 80 (1MHz), count up
  timerAttachInterrupt(watchdogTimer, &watchdogInterrupt);
  timerAlarmWrite(watchdogTimer, watchdogTimeout * 1000, true); // 60 seconds in microseconds
  timerAlarmEnable(watchdogTimer);
  lastWatchdogFeed = millis();
  Serial.println("Watchdog timer initialized (60s timeout)");
}

void feedWatchdog() {
  timerWrite(watchdogTimer, 0); // Reset timer
  lastWatchdogFeed = millis();
}

// Read battery voltage
float readBatteryVoltage() {
  // Read ADC value
  int adcValue = analogRead(BATTERY_ADC_PIN);
  
  // Convert to voltage (assuming voltage divider if needed)
  float voltage = (adcValue * ADC_REF_VOLTAGE) / (1 << BATTERY_ADC_RESOLUTION);
  voltage = voltage * VOLTAGE_DIVIDER_RATIO; // Adjust if using voltage divider
  
  return voltage;
}

// Check solar charging status
bool checkSolarCharging() {
  // Read solar charge pin (HIGH = charging, LOW = not charging)
  // This depends on your solar charger circuit
  return digitalRead(SOLAR_CHARGE_PIN) == HIGH;
}

// Read door state from reed switch
bool readDoorState() {
  // Reed switch: LOW = door closed (magnet near), HIGH = door open (magnet away)
  // This may need to be inverted depending on your wiring
  return digitalRead(REED_SWITCH_PIN) == HIGH;
}

// Deep sleep function with IR sensor wake-up
void enterDeepSleep(unsigned long sleepSeconds = 0) {
  Serial.println("Preparing for deep sleep...");
  
  // Read final battery status
  batteryVoltage = readBatteryVoltage();
  solarCharging = checkSolarCharging();
  
  Serial.printf("Battery voltage: %.2fV\n", batteryVoltage);
  Serial.printf("Solar charging: %s\n", solarCharging ? "Yes" : "No");
  
  // Disable watchdog before sleep
  if (watchdogTimer) {
    timerAlarmDisable(watchdogTimer);
  }
  
  // Disable WiFi to save power
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  
  // Turn off LED
  digitalWrite(LED_STATUS_PIN, LOW);
  
  // Configure wake-up sources
  // 1. Wake on IR sensor interrupt (GPIO 13) - HIGH trigger
  esp_sleep_enable_ext0_wakeup((gpio_num_t)IR_SENSOR_PIN, 1); // 1 = HIGH level
  
  // 2. Wake on timer (backup wake-up every hour)
  if (sleepSeconds > 0) {
    esp_sleep_enable_timer_wakeup(sleepSeconds * 1000000ULL); // Convert to microseconds
  } else {
    esp_sleep_enable_timer_wakeup(deepSleepDuration * 1000ULL); // Default 1 hour
  }
  
  Serial.printf("Entering deep sleep... (Wake on IR sensor GPIO %d or timer)\n", IR_SENSOR_PIN);
  Serial.flush();
  delay(100);
  
  // Enter deep sleep
  esp_deep_sleep_start();
}

// Load WiFi credentials from flash
bool loadWiFiCredentials() {
  preferences.begin("wifi", false);
  wifiSSID = preferences.getString("ssid", "");
  wifiPassword = preferences.getString("password", "");
  preferences.end();
  
  return wifiSSID.length() > 0;
}

// Save WiFi credentials to flash
void saveWiFiCredentials(String ssid, String password) {
  preferences.begin("wifi", false);
  preferences.putString("ssid", ssid);
  preferences.putString("password", password);
  preferences.end();
  Serial.println("WiFi credentials saved to flash");
}

// HTML form for WiFi configuration
const char* configHTML = R"(
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Camera Setup</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #333;
            margin-bottom: 8px;
            font-size: 14px;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-size: 14px;
        }
        .success {
            background: #d4edda;
            color: #155724;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📷 Smart Camera Setup</h1>
        <p class="subtitle">Connect your camera to WiFi</p>
        <form action="/config" method="POST">
            <div class="form-group">
                <label for="ssid">WiFi Network Name (SSID)</label>
                <input type="text" id="ssid" name="ssid" required autocomplete="off">
            </div>
            <div class="form-group">
                <label for="password">WiFi Password</label>
                <input type="password" id="password" name="password" autocomplete="off">
            </div>
            <button type="submit">Connect & Reboot</button>
        </form>
        <div id="status"></div>
    </div>
    <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status';
            statusDiv.textContent = 'Connecting...';
            statusDiv.style.display = 'block';
            
            fetch('/config', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(data => {
                statusDiv.className = 'status success';
                statusDiv.innerHTML = '✓ WiFi configured! Device will reboot in 3 seconds...';
                setTimeout(() => {
                    statusDiv.innerHTML = 'Rebooting...';
                }, 3000);
            })
            .catch(error => {
                statusDiv.className = 'status error';
                statusDiv.textContent = 'Error: ' + error;
            });
        });
    </script>
</body>
</html>
)";

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return false;
  }
  
  sensor_t * s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  
  Serial.println("Camera initialized successfully!");
  return true;
}

void setupAPMode() {
  Serial.println("Setting up Access Point mode for initial configuration...");
  
  // Use fixed AP SSID for setup: "SmartCamera-SETUP"
  // This makes it easier for customers to find during initial setup
  // Customer just needs to turn on the device, no cables or plugging in required
  String apName = String(apSSID);
  
  WiFi.mode(WIFI_AP);
  WiFi.softAP(apName.c_str(), apPassword);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.println("========================================");
  Serial.println("SETUP MODE ACTIVE");
  Serial.println("========================================");
  Serial.print("WiFi Network Name: ");
  Serial.println(apName);
  Serial.print("Setup Page: ");
  Serial.println("http://192.168.4.1/config");
  Serial.println("========================================");
  Serial.println("Instructions:");
  Serial.println("1. Turn on device (LED should blink)");
  Serial.println("2. Connect phone/computer to WiFi: SmartCamera-SETUP");
  Serial.println("3. Open browser and go to: http://192.168.4.1/config");
  Serial.println("4. Enter your home WiFi credentials");
  Serial.println("5. Device will reboot and connect automatically");
  Serial.println("========================================");
  
  // Setup web server routes
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/html", String(configHTML));
  });
  
  server.on("/config", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send(200, "text/html", String(configHTML));
  });
  
  server.on("/config", HTTP_POST, [](AsyncWebServerRequest *request){
    if (request->hasParam("ssid", true) && request->hasParam("password", true)) {
      String ssid = request->getParam("ssid", true)->value();
      String password = request->getParam("password", true)->value();
      
      Serial.println("Received WiFi credentials:");
      Serial.println("SSID: " + ssid);
      Serial.println("Password: " + password);
      
      // Save credentials
      saveWiFiCredentials(ssid, password);
      
      request->send(200, "text/html", 
        "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<title>Success</title><style>body{font-family:sans-serif;display:flex;align-items:center;"
        "justify-content:center;min-height:100vh;background:#667eea;color:white;text-align:center;}"
        "h1{margin-bottom:20px;}</style></head><body><div><h1>✓ Success!</h1>"
        "<p>WiFi credentials saved. Device will reboot in 3 seconds...</p></div></body></html>");
      
      delay(3000);
      ESP.restart();
    } else {
      request->send(400, "text/plain", "Missing SSID or password");
    }
  });
  
  server.begin();
  apMode = true;
  Serial.println("Web server started");
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(wifiSSID);
  setLEDStatus(LED_WIFI_CONNECTING);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSSID.c_str(), wifiPassword.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    updateLED(); // Update LED during connection
    feedWatchdog(); // Feed watchdog
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    apMode = false;
    setLEDStatus(LED_WIFI_CONNECTED);
  } else {
    Serial.println();
    Serial.println("WiFi connection failed! Entering AP mode...");
    setLEDStatus(LED_ERROR);
    setupAPMode();
  }
}

String takePhoto() {
  if (!cameraInitialized) {
    Serial.println("Camera not initialized!");
    return "";
  }
  
  Serial.println("Capturing photo...");
  
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return "";
  }
  
  Serial.printf("Picture taken! Size: %zu bytes\n", fb->len);
  
  int base64Length = Base64.encodedLength(fb->len);
  char *base64Buffer = (char*)malloc(base64Length + 1);
  
  if (base64Buffer == NULL) {
    Serial.println("Memory allocation failed for base64 buffer");
    esp_camera_fb_return(fb);
    return "";
  }
  
  Base64.encode(base64Buffer, (char*)fb->buf, fb->len);
  base64Buffer[base64Length] = '\0';
  
  String base64String = String(base64Buffer);
  
  free(base64Buffer);
  esp_camera_fb_return(fb);
  
  Serial.printf("Base64 encoded length: %d\n", base64String.length());
  return base64String;
}

void uploadPhoto(String base64Image, bool motionDetected = false) {
  uploadPhotoWithMetadata(base64Image, motionDetected, doorOpen, batteryVoltage, solarCharging);
}

void uploadPhotoWithMetadata(String base64Image, bool motionDetected, bool doorState, float batteryVolt, bool solarCharge) {
  if (base64Image.length() == 0) {
    Serial.println("Upload: Failed - Empty image data");
    isUploading = false;
    return;
  }
  
  // Check connection status
  if (apMode) {
    Serial.println("Upload: Failed - In AP mode");
    isUploading = false;
    return;
  }
  
  // Set upload flag to prevent false triggers
  isUploading = true;
  
  // Check WiFi status periodically
  checkWiFiStatus();
  
  // Cellular-first connectivity: Try cellular first, WiFi as fallback
  bool connected = false;
  
  // 1. Try cellular first (A7670)
  if (connectCellular()) {
    connected = true;
    currentConnection = CONN_CELLULAR;
    Serial.println("Using cellular connection (A7670)");
  }
  // 2. Fallback to WiFi if strong signal
  else if (shouldUseWiFi()) {
    if (WiFi.status() == WL_CONNECTED) {
      connected = true;
      currentConnection = CONN_WIFI;
      Serial.println("Using WiFi connection (fallback)");
    }
  }
  
  if (!connected) {
    Serial.println("Upload: Failed - No connection available (cellular and WiFi failed)");
    isUploading = false;
    // TODO: Save to SD card for retry later
    return;
  }
  
  HTTPClient http;
  String url = buildApiUrl(API_ENDPOINT);
  
  Serial.print("Uploading photo to: ");
  Serial.println(url);
  if (motionDetected) {
    Serial.println("Motion-triggered capture");
  }
  
  // Use HTTPS for domains, HTTP for IP addresses
  if (isIPAddress(API_DOMAIN)) {
    // Use regular HTTP client for IP addresses
    http.begin(url);
  } else {
    // Use secure client for domains
    WiFiClientSecure client;
    configureSSLClient(client);
    http.begin(client, url);
  }
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(30000);  // 30 second timeout for large uploads
  
  StaticJsonDocument<50000> doc;
  doc["serial"] = serialNumber;
  doc["image"] = base64Image;
  doc["motion_detected"] = motionDetected;
  doc["door_open"] = doorState;
  doc["battery_voltage"] = batteryVolt;
  doc["solar_charging"] = solarCharge;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0 && httpResponseCode < 400) {
    Serial.println("Upload: Success");
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
  } else {
    Serial.println("Upload: Failed");
    Serial.print("HTTP Error code: ");
    Serial.println(httpResponseCode);
    
    // Handle SSL errors
    if (httpResponseCode == -1) {
      Serial.println("SSL/TLS connection error - check certificate and domain");
    }
  }
  
  http.end();
}

void sendHeartbeat() {
  // Check connection status
  if (apMode) {
    return;
  }
  
  // Check WiFi status periodically
  checkWiFiStatus();
  
  // Use cellular if WiFi is not connected
  if (WiFi.status() != WL_CONNECTED) {
    if (currentConnection != CONN_CELLULAR) {
      if (!connectCellular()) {
        return; // No connection available
      }
    }
  } else {
    currentConnection = CONN_WIFI;
  }
  
  HTTPClient http;
  String url = buildApiUrl(HEARTBEAT_ENDPOINT);
  
  Serial.print("Sending heartbeat to: ");
  Serial.println(url);
  
  // Use HTTPS for domains, HTTP for IP addresses
  if (isIPAddress(API_DOMAIN)) {
    // Use regular HTTP client for IP addresses
    http.begin(url);
  } else {
    // Use secure client for domains
    WiFiClientSecure client;
    configureSSLClient(client);
    http.begin(client, url);
  }
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);  // 10 second timeout
  
  StaticJsonDocument<200> doc;
  doc["serial_number"] = serialNumber;
  doc["connection_type"] = (currentConnection == CONN_CELLULAR) ? "cellular" : "wifi";
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    lastUploadTime = millis(); // Update last upload time
  } else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
    if (httpResponseCode == -1) {
      Serial.println("SSL/TLS connection error");
    }
  }
  
  http.end();
}

void sendPhoto(bool isMotionTriggered = false) {
  // Check connection status
  if (apMode) {
    return;
  }
  
  // Feed watchdog
  feedWatchdog();
  
  // Check WiFi status periodically
  checkWiFiStatus();
  
  // Use cellular if WiFi is not connected
  if (WiFi.status() != WL_CONNECTED) {
    if (currentConnection != CONN_CELLULAR) {
      if (!connectCellular()) {
        setLEDStatus(LED_ERROR);
        return; // No connection available
      } else {
        setLEDStatus(LED_CELLULAR_ACTIVE);
      }
    }
  } else {
    currentConnection = CONN_WIFI;
    setLEDStatus(LED_WIFI_CONNECTED);
  }
  
  if (!cameraInitialized) {
    Serial.println("Camera not initialized. Cannot capture photo.");
    setLEDStatus(LED_ERROR);
    return;
  }
  
  if (isMotionTriggered) {
    Serial.println("Motion detected! Starting photo capture and upload...");
    setLEDStatus(LED_MOTION);
  } else {
    Serial.println("Starting scheduled photo capture and upload...");
    setLEDStatus(LED_CAPTURING);
  }
  
  String base64Image = takePhoto();
  
  if (base64Image.length() == 0) {
    Serial.println("Failed to capture photo");
    return;
  }
  
  HTTPClient http;
  String url = buildApiUrl(API_ENDPOINT);
  
  Serial.print("Sending photo to: ");
  Serial.println(url);
  
  // Use HTTPS for domains, HTTP for IP addresses
  if (isIPAddress(API_DOMAIN)) {
    // Use regular HTTP client for IP addresses
    http.begin(url);
  } else {
    // Use secure client for domains
    WiFiClientSecure client;
    configureSSLClient(client);
    http.begin(client, url);
  }
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(30000);  // 30 second timeout for large uploads
  
  StaticJsonDocument<50000> doc;
  doc["serial"] = serialNumber;
  doc["image"] = base64Image;
  doc["motion_detected"] = isMotionTriggered;
  doc["connection_type"] = (currentConnection == CONN_CELLULAR) ? "cellular" : "wifi";
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.printf("Payload size: %d bytes\n", jsonPayload.length());
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0 && httpResponseCode < 400) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    lastUploadTime = millis(); // Update last upload time
  } else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
    if (httpResponseCode == -1) {
      Serial.println("SSL/TLS connection error");
    }
  }
  
  http.end();
}

// SIM7600 Cellular Functions
void powerOnSIM7600() {
  Serial.println("Powering on SIM7600...");
  pinMode(SIM7600_POWER_PIN, OUTPUT);
  digitalWrite(SIM7600_POWER_PIN, LOW);
  delay(1000);
  digitalWrite(SIM7600_POWER_PIN, HIGH);
  delay(2000);
  digitalWrite(SIM7600_POWER_PIN, LOW);
  delay(3000);
  Serial.println("SIM7600 power sequence completed");
}

String sendATCommand(String command, unsigned long timeout = 2000) {
  sim7600Serial.print(command);
  sim7600Serial.print("\r\n");
  
  unsigned long startTime = millis();
  String response = "";
  
  while (millis() - startTime < timeout) {
    if (sim7600Serial.available()) {
      char c = sim7600Serial.read();
      response += c;
      if (response.endsWith("OK\r\n") || response.endsWith("ERROR\r\n")) {
        break;
      }
    }
  }
  
  return response;
}

bool initSIM7600() {
  Serial.println("Initializing SIM7600...");
  
  // Initialize serial communication
  sim7600Serial.begin(SIM7600_BAUD, SERIAL_8N1, SIM7600_RX_PIN, SIM7600_TX_PIN);
  delay(2000);
  
  // Power on module
  powerOnSIM7600();
  delay(5000);
  
  // Test AT command
  String response = sendATCommand("AT", 3000);
  if (response.indexOf("OK") == -1) {
    Serial.println("SIM7600 not responding to AT commands");
    return false;
  }
  Serial.println("SIM7600 responding");
  
  // Check SIM card
  response = sendATCommand("AT+CPIN?", 5000);
  if (response.indexOf("READY") == -1) {
    Serial.println("SIM card not ready");
    return false;
  }
  Serial.println("SIM card ready");
  
  // Set network mode to LTE
  sendATCommand("AT+CNMP=38", 3000); // 38 = LTE only
  
  // Set APN
  String apnCmd = "AT+CGDCONT=1,\"IP\",\"" + String(cellularAPN) + "\"";
  sendATCommand(apnCmd, 3000);
  
  // Activate PDP context
  response = sendATCommand("AT+CGACT=1,1", 10000);
  if (response.indexOf("OK") == -1) {
    Serial.println("Failed to activate PDP context");
    return false;
  }
  
  // Get IP address
  response = sendATCommand("AT+CGPADDR=1", 5000);
  Serial.print("Cellular IP response: ");
  Serial.println(response);
  
  Serial.println("SIM7600 initialized successfully");
  return true;
}

bool connectCellular() {
  if (!cellularEnabled) {
    if (!initSIM7600()) {
      return false;
    }
    cellularEnabled = true;
  }
  
  // Check network registration
  String response = sendATCommand("AT+CREG?", 5000);
  if (response.indexOf("0,1") == -1 && response.indexOf("0,5") == -1) {
    Serial.println("Not registered to network");
    return false;
  }
  
  // Check GPRS registration
  response = sendATCommand("AT+CGREG?", 5000);
  if (response.indexOf("0,1") == -1 && response.indexOf("0,5") == -1) {
    Serial.println("GPRS not registered");
    return false;
  }
  
  Serial.println("Cellular connection established");
  currentConnection = CONN_CELLULAR;
  return true;
}

void checkWiFiStatus() {
  static unsigned long lastCheck = 0;
  unsigned long currentTime = millis();
  
  // Check WiFi status every 30 seconds
  if (currentTime - lastCheck < 30000) {
    return;
  }
  lastCheck = currentTime;
  
  if (WiFi.status() == WL_CONNECTED) {
    // WiFi is connected
    if (wifiFailureStartTime > 0) {
      Serial.println("WiFi reconnected, disabling cellular");
      wifiFailureStartTime = 0;
      currentConnection = CONN_WIFI;
    }
  } else {
    // WiFi is disconnected
    if (wifiFailureStartTime == 0) {
      wifiFailureStartTime = currentTime;
      Serial.println("WiFi disconnected, starting failure timer");
    } else {
      unsigned long failureDuration = currentTime - wifiFailureStartTime;
      if (failureDuration >= wifiFailureTimeout && !cellularEnabled) {
        Serial.println("WiFi failed for 5 minutes, switching to cellular...");
        if (connectCellular()) {
          Serial.println("Switched to cellular connection");
        } else {
          Serial.println("Failed to connect via cellular");
        }
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Check wake-up reason
  wakeupReason = esp_sleep_get_wakeup_cause();
  wokeFromDeepSleep = (wakeupReason != ESP_SLEEP_WAKEUP_UNDEFINED);
  
  Serial.println("ESP32-CAM Smart Camera Firmware");
  Serial.println("====================");
  Serial.println("Device powered on - Initializing...");
  
  if (wokeFromDeepSleep) {
    Serial.println("Woke from deep sleep!");
    switch(wakeupReason) {
      case ESP_SLEEP_WAKEUP_EXT0:
        Serial.println("Wake reason: IR sensor interrupt (GPIO 13)");
        mailDetected = true;
        break;
      case ESP_SLEEP_WAKEUP_TIMER:
        Serial.println("Wake reason: Timer");
        break;
      default:
        Serial.printf("Wake reason: %d\n", wakeupReason);
        break;
    }
  } else {
    Serial.println("Device turned on - First boot");
    Serial.println("LED should start blinking to indicate device is working");
  }
  
  Serial.println("Type 'help' for available commands");
  
  // Get device serial number
  serialNumber = getDeviceSerial();
  Serial.print("Device Serial: ");
  Serial.println(serialNumber);
  
  // Initialize camera
  Serial.println("Initializing camera...");
  cameraInitialized = initCamera();
  
  if (!cameraInitialized) {
    Serial.println("WARNING: Camera initialization failed. Photo capture will not work.");
  }
  
  // Initialize IR sensor for mail detection
  pinMode(IR_SENSOR_PIN, INPUT_PULLDOWN); // Pull-down to ensure stable reading
  
  // Power on IR sensor (if using power control)
  powerOnIRSensor();
  
  // Initialize light sensor (if available)
  pinMode(LIGHT_SENSOR_PIN, INPUT);
  checkDaytime();
  
  Serial.println("IR sensor initialized on GPIO 13");
  Serial.printf("Light sensor initialized - Level: %.0f, Daytime: %s\n", 
                lightLevel, isDaytime ? "Yes" : "No");
  
  // Initialize reed switch for door state
  pinMode(REED_SWITCH_PIN, INPUT_PULLUP); // Pull-up for reed switch
  doorOpen = readDoorState();
  Serial.printf("Reed switch initialized on GPIO 12 - Door: %s\n", doorOpen ? "OPEN" : "CLOSED");
  
  // Initialize battery monitoring (for battery-powered standalone operation)
  // Device works on battery power - just turn it on, no USB cable needed
  pinMode(BATTERY_ADC_PIN, INPUT);
  analogSetAttenuation(ADC_11db); // 0-3.3V range
  batteryVoltage = readBatteryVoltage();
  Serial.printf("Battery monitoring initialized - Voltage: %.2fV\n", batteryVoltage);
  if (batteryVoltage < BATTERY_LOW_THRESHOLD) {
    Serial.println("WARNING: Low battery voltage detected!");
  } else {
    Serial.println("Battery level OK - Device ready for operation");
  }
  if (batteryVoltage < BATTERY_LOW_THRESHOLD) {
    Serial.println("WARNING: Low battery voltage detected!");
  } else {
    Serial.println("Battery level OK - Device ready for operation");
  }
  
  // Initialize solar charging status pin
  pinMode(SOLAR_CHARGE_PIN, INPUT);
  solarCharging = checkSolarCharging();
  Serial.printf("Solar charging status on GPIO 15 - Charging: %s\n", solarCharging ? "Yes" : "No");
  
  // Initialize LED status indicator
  // LED will blink to show device is working when turned on
  pinMode(LED_STATUS_PIN, OUTPUT);
  digitalWrite(LED_STATUS_PIN, LOW);
  setLEDStatus(LED_WIFI_CONNECTING);
  Serial.println("LED status indicator initialized - LED blinking indicates device is on and working");
  
  // Initialize watchdog timer
  initWatchdog();
  
  // Initialize last activity time
  lastActivityTime = millis();
  
  // Initialize A7670 (cellular-first, will connect if needed)
  // Don't power on yet - will power on when needed
  Serial.println("A7670 cellular module ready (will connect on demand)");
  
  // Load WiFi credentials
  if (loadWiFiCredentials()) {
    Serial.println("WiFi credentials found, connecting to home network...");
    setLEDStatus(LED_WIFI_CONNECTING);
    connectToWiFi();
    if (WiFi.status() == WL_CONNECTED) {
      currentConnection = CONN_WIFI;
      setLEDStatus(LED_WIFI_CONNECTED);
      Serial.println("✓ Connected to WiFi - Device is online!");
    } else {
      setLEDStatus(LED_ERROR);
      Serial.println("WiFi connection failed - Will try cellular if available");
    }
  } else {
    Serial.println("No WiFi credentials found - Starting setup mode...");
    Serial.println("Device will create WiFi network: SmartCamera-SETUP");
    Serial.println("Connect to this network and go to: http://192.168.4.1/config");
    setLEDStatus(LED_ERROR); // Blinking LED indicates setup mode
    setupAPMode();
  }
  
  // Initial heartbeat and capture after connection
  if ((WiFi.status() == WL_CONNECTED && !apMode) || currentConnection == CONN_CELLULAR) {
    lastHeartbeat = millis() - heartbeatInterval;
    lastCapture = millis() - captureInterval;
  }
}

// Serial command handlers
void handleSerialCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialInput.length() > 0) {
        processSerialCommand(serialInput);
        serialInput = "";
      }
    } else {
      serialInput += c;
    }
  }
}

void processSerialCommand(String command) {
  command.toLowerCase();
  command.trim();
  
  Serial.println("\n=== Command: " + command + " ===");
  
  if (command == "status") {
    printStatus();
  } else if (command == "test") {
    testPhotoCapture();
  } else if (command == "reset") {
    resetWiFiSettings();
  } else if (command == "help") {
    printHelp();
  } else {
    Serial.println("Unknown command. Type 'help' for available commands.");
  }
}

void printStatus() {
  Serial.println("\n--- Device Status ---");
  Serial.print("Serial Number: ");
  Serial.println(serialNumber);
  Serial.print("Firmware Version: ");
  Serial.println(currentFirmwareVersion);
  Serial.print("Camera Initialized: ");
  Serial.println(cameraInitialized ? "Yes" : "No");
  
  Serial.println("\n--- Connection Status ---");
  if (apMode) {
    Serial.println("Mode: Access Point");
    Serial.print("AP SSID: ");
    Serial.println(String(apSSID) + serialNumber.substring(4));
    Serial.println("AP IP: 192.168.4.1");
  } else {
    Serial.print("Connection Type: ");
    if (currentConnection == CONN_WIFI) {
      Serial.println("WiFi");
      Serial.print("WiFi SSID: ");
      Serial.println(wifiSSID);
      Serial.print("WiFi Status: ");
      if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Connected");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.print("RSSI: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
      } else {
        Serial.println("Disconnected");
      }
    } else if (currentConnection == CONN_CELLULAR) {
      Serial.println("Cellular (SIM7600)");
      Serial.println("Cellular Enabled: Yes");
    } else {
      Serial.println("None");
    }
  }
  
  Serial.println("\n--- Timing ---");
  unsigned long uptime = millis() / 1000;
  Serial.print("Uptime: ");
  Serial.print(uptime / 3600);
  Serial.print("h ");
  Serial.print((uptime % 3600) / 60);
  Serial.print("m ");
  Serial.print(uptime % 60);
  Serial.println("s");
  
  if (lastUploadTime > 0) {
    unsigned long timeSinceUpload = (millis() - lastUploadTime) / 1000;
    Serial.print("Last Upload: ");
    Serial.print(timeSinceUpload);
    Serial.println(" seconds ago");
  } else {
    Serial.println("Last Upload: Never");
  }
  
  Serial.print("Next Heartbeat: ");
  unsigned long timeToHeartbeat = (heartbeatInterval - (millis() - lastHeartbeat)) / 1000;
  Serial.print(timeToHeartbeat);
  Serial.println(" seconds");
  
  Serial.print("Next Capture: ");
  unsigned long timeToCapture = (captureInterval - (millis() - lastCapture)) / 1000;
  Serial.print(timeToCapture);
  Serial.println(" seconds");
  
  Serial.println("\n--- Mailbox Sensors ---");
  int irReading = digitalRead(IR_SENSOR_PIN);
  Serial.print("IR Sensor (GPIO 13): ");
  Serial.println(irReading == HIGH ? "Mail Detected" : "No Mail");
  Serial.print("Mail Detected Flag: ");
  Serial.println(mailDetected ? "Yes" : "No");
  
  bool doorState = readDoorState();
  Serial.print("Reed Switch (GPIO 12): ");
  Serial.println(doorState ? "Door OPEN" : "Door CLOSED");
  
  Serial.println("\n--- Power Management ---");
  Serial.printf("Battery Voltage: %.2fV\n", batteryVoltage);
  Serial.printf("Solar Charging: %s\n", solarCharging ? "Yes" : "No");
  if (batteryVoltage < BATTERY_LOW_THRESHOLD) {
    Serial.println("WARNING: Low battery!");
  }
  
  Serial.println("\n--- Deep Sleep Status ---");
  Serial.printf("Deep Sleep Enabled: %s\n", deepSleepEnabled ? "Yes" : "No");
  Serial.printf("Woke From Deep Sleep: %s\n", wokeFromDeepSleep ? "Yes" : "No");
  if (wokeFromDeepSleep) {
    Serial.printf("Wake Reason: %d\n", wakeupReason);
  }
  unsigned long timeToSleep = (deepSleepDuration - (millis() - lastActivityTime)) / 1000;
  Serial.printf("Time until sleep: %lu seconds\n", timeToSleep);
  
  Serial.println("==================\n");
}

void testPhotoCapture() {
  Serial.println("\n--- Test Photo Capture ---");
  
  if (!cameraInitialized) {
    Serial.println("ERROR: Camera not initialized!");
    return;
  }
  
  if (apMode) {
    Serial.println("ERROR: Cannot upload in AP mode!");
    return;
  }
  
  Serial.println("Capturing photo...");
  sendPhoto(false);
  Serial.println("Test photo capture completed!");
  Serial.println("==================\n");
}

void resetWiFiSettings() {
  Serial.println("\n--- Reset WiFi Settings ---");
  Serial.println("WARNING: This will clear all saved WiFi credentials!");
  Serial.println("Clearing WiFi settings...");
  
  preferences.begin("wifi", false);
  preferences.clear();
  preferences.end();
  
  Serial.println("WiFi settings cleared. Device will reboot in 3 seconds...");
  delay(3000);
  ESP.restart();
}

void printHelp() {
  Serial.println("\n=== Available Commands ===");
  Serial.println("status  - Show device status and connection info");
  Serial.println("test    - Take and upload a test photo");
  Serial.println("reset   - Clear WiFi settings and reboot");
  Serial.println("help    - Show this help message");
  Serial.println("========================\n");
}

void loop() {
  // Feed watchdog regularly
  if (millis() - lastWatchdogFeed > 10000) { // Feed every 10 seconds
    feedWatchdog();
  }
  
  // Update LED status indicator
  updateLED();
  
  // Handle serial commands
  handleSerialCommands();
  
  // In AP mode, just handle web server requests
  if (apMode) {
    delay(100);
    return;
  }
  
  // Check WiFi status and switch to cellular if needed
  checkWiFiStatus();
  
  // Normal operation mode
  unsigned long currentTime = millis();
  
  // Check door state (reed switch on GPIO 12)
  bool currentDoorState = readDoorState();
  if (currentDoorState != doorOpen) {
    // Debounce door state changes
    if (currentTime - lastDoorStateChange >= doorDebounceInterval) {
      doorOpen = currentDoorState;
      lastDoorStateChange = currentTime;
      Serial.printf("Door state changed: %s\n", doorOpen ? "OPEN" : "CLOSED");
      
      // Update battery and solar status
      batteryVoltage = readBatteryVoltage();
      solarCharging = checkSolarCharging();
    }
  }
  
  // Check if we've been awake too long (30 second limit)
  if (wakeTime > 0 && (currentTime - wakeTime) > MAX_AWAKE_TIME) {
    Serial.println("Max awake time (30s) reached. Returning to deep sleep...");
    enterDeepSleep();
    return;
  }
  
  // Ignore IR triggers during upload process
  if (isUploading) {
    return;
  }
  
  // Check IR sensor for mail detection (GPIO 13)
  int irReading = digitalRead(IR_SENSOR_PIN);
  
  // If woke from deep sleep due to IR sensor
  if (wokeFromDeepSleep && wakeupReason == ESP_SLEEP_WAKEUP_EXT0) {
    // Record wake time
    wakeTime = currentTime;
    wokeFromDeepSleep = false; // Clear flag
    
    // First trigger detected - start consecutive trigger detection
    firstTriggerDetected = true;
    firstTriggerTime = currentTime;
    
    Serial.println("IR sensor triggered wake-up - Waiting for confirmation trigger...");
    Serial.println("Requiring 2 consecutive triggers within 5 seconds to prevent false positives");
    
    // Wait briefly and check for second trigger
    delay(100);
    irReading = digitalRead(IR_SENSOR_PIN);
    
    // If still HIGH after brief delay, consider it a valid first trigger
    if (irReading == HIGH) {
      Serial.println("First trigger confirmed - waiting for second trigger...");
    } else {
      Serial.println("First trigger may be false - resetting...");
      firstTriggerDetected = false;
      firstTriggerTime = 0;
    }
    
    return; // Wait for second trigger in next loop iteration
  }
  
  // Check for second consecutive trigger (false positive prevention)
  if (firstTriggerDetected && irReading == HIGH) {
    unsigned long timeSinceFirstTrigger = currentTime - firstTriggerTime;
    
    if (timeSinceFirstTrigger <= CONSECUTIVE_TRIGGER_WINDOW) {
      // Second trigger within window - valid mail detection!
      Serial.println("Second trigger confirmed! Mail detected.");
      mailDetected = true;
      firstTriggerDetected = false; // Reset
      firstTriggerTime = 0;
      
      // Check day/night status
      checkDaytime();
      Serial.printf("Light level: %.0f, Daytime: %s\n", lightLevel, isDaytime ? "Yes" : "No");
      
      // Ensure WiFi is connected
      if (WiFi.status() != WL_CONNECTED && !apMode) {
        connectToWiFi();
      }
      
      // Set upload flag to prevent false triggers during upload
      isUploading = true;
      setLEDStatus(LED_MOTION);
      
      // Take 3 photos with 1 second interval
      Serial.println("Taking 3 photos (1 second apart)...");
      for (int i = 0; i < PHOTOS_PER_TRIGGER; i++) {
        Serial.printf("Taking photo %d of %d...\n", i + 1, PHOTOS_PER_TRIGGER);
        setLEDStatus(LED_CAPTURING);
        
        String base64Image = takePhoto();
        if (base64Image.length() > 0) {
          // Upload with door state and battery info
          uploadPhotoWithMetadata(base64Image, true, doorOpen, batteryVoltage, solarCharging);
          Serial.printf("Photo %d uploaded successfully\n", i + 1);
        } else {
          Serial.printf("Failed to capture photo %d\n", i + 1);
        }
        
        // 1 second delay between photos (except for the last one)
        if (i < PHOTOS_PER_TRIGGER - 1) {
          delay(1000); // 1 second as specified
        }
      }
      
      // Clear upload flag
      isUploading = false;
      
      mailDetected = false;
      lastMotionTrigger = currentTime;
      lastActivityTime = currentTime;
      wakeTime = 0; // Reset wake time
      
      Serial.println("Mail detection complete. Returning to deep sleep...");
      delay(1000); // Brief delay to ensure uploads complete
      enterDeepSleep();
      return; // Should not reach here, but just in case
    } else {
      // Timeout - first trigger was likely false positive
      Serial.println("Second trigger timeout - first trigger was false positive");
      firstTriggerDetected = false;
      firstTriggerTime = 0;
      
      // Return to sleep if we've been awake too long
      if ((currentTime - wakeTime) > MAX_AWAKE_TIME) {
        Serial.println("Max awake time reached. Returning to deep sleep...");
        enterDeepSleep();
        return;
      }
    }
  }
  
  // Check if first trigger window expired
  if (firstTriggerDetected && (currentTime - firstTriggerTime) > CONSECUTIVE_TRIGGER_WINDOW) {
    Serial.println("First trigger window expired - false positive detected");
    firstTriggerDetected = false;
    firstTriggerTime = 0;
    
    // Return to sleep
    if ((currentTime - wakeTime) > 5000) { // Wait at least 5 seconds
      Serial.println("Returning to deep sleep...");
      enterDeepSleep();
      return;
    }
  }
  
  // Normal operation IR sensor check (if not in deep sleep mode)
  if (!deepSleepEnabled) {
    if (irReading == HIGH && !mailDetected && !firstTriggerDetected) {
      // IR sensor triggered during normal operation
      mailDetected = true;
      Serial.println("Mail detected on IR sensor!");
      setLEDStatus(LED_MOTION);
      
      // Debounce logic: only trigger if 5 seconds have passed since last trigger
      if (currentTime - lastMotionTrigger >= motionDebounceInterval) {
        Serial.println("Taking 3 photos...");
        isUploading = true;
        
        // Take 3 photos
        for (int i = 0; i < PHOTOS_PER_TRIGGER; i++) {
          Serial.printf("Taking photo %d of %d...\n", i + 1, PHOTOS_PER_TRIGGER);
          setLEDStatus(LED_CAPTURING);
          
          String base64Image = takePhoto();
          if (base64Image.length() > 0) {
            uploadPhotoWithMetadata(base64Image, true, doorOpen, batteryVoltage, solarCharging);
          }
          
          if (i < PHOTOS_PER_TRIGGER - 1) {
            delay(1000); // 1 second between photos
          }
        }
        
        isUploading = false;
        lastMotionTrigger = currentTime;
        lastCapture = currentTime;
        lastActivityTime = currentTime;
      }
    } else if (irReading == LOW && mailDetected) {
      mailDetected = false;
      Serial.println("Mail cleared");
      setLEDStatus(currentConnection == CONN_CELLULAR ? LED_CELLULAR_ACTIVE : LED_WIFI_CONNECTED);
    }
  }
  
  // Update battery and solar status periodically
  static unsigned long lastBatteryCheck = 0;
  if (currentTime - lastBatteryCheck >= 60000) { // Check every minute
    batteryVoltage = readBatteryVoltage();
    solarCharging = checkSolarCharging();
    lastBatteryCheck = currentTime;
    
    // Check for low battery
    if (batteryVoltage < BATTERY_LOW_THRESHOLD && !solarCharging) {
      Serial.printf("WARNING: Low battery voltage: %.2fV\n", batteryVoltage);
      setLEDStatus(LED_ERROR);
    }
  }
  
  // Check if it's time to send heartbeat (only if not in deep sleep mode)
  if (!deepSleepEnabled && currentTime - lastHeartbeat >= heartbeatInterval) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
    lastActivityTime = currentTime;
  }
  
  // Scheduled captures disabled for mailbox mode - only IR sensor triggers
  // (Uncomment below if you want periodic captures in addition to IR triggers)
  /*
  if (currentTime - lastCapture >= captureInterval) {
    String base64Image = takePhoto();
    if (base64Image.length() > 0) {
      uploadPhotoWithMetadata(base64Image, false, doorOpen, batteryVoltage, solarCharging);
    }
    lastCapture = currentTime;
    lastActivityTime = currentTime;
  }
  */
  
  // Deep sleep check for mailbox mode
  // Enter deep sleep if no activity for configured duration
  // This ensures the device sleeps between mail detections
  if (deepSleepEnabled) {
    // If we just finished processing mail detection, enter sleep immediately
    if (mailDetected && (currentTime - lastMotionTrigger) > 10000) {
      Serial.println("Mail processing complete. Entering deep sleep...");
      delay(1000); // Brief delay to ensure everything is saved
      enterDeepSleep();
      return;
    }
    
    // Otherwise, enter sleep after inactivity period
    if (currentTime - lastActivityTime >= deepSleepDuration) {
      Serial.println("No activity detected, entering deep sleep...");
      Serial.println("Device will wake on IR sensor trigger or timer");
      enterDeepSleep();
      return;
    }
  }
  
  delay(100);
}
