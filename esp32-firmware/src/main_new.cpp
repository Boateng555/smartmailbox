#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>
#include <Preferences.h>
#include <ESPAsyncWebServer.h>
#include "esp_camera.h"
#include "Base64.h"
#include <esp_sleep.h>

// ============================================================================
// CONFIGURATION SECTION
// ============================================================================

// Replace with your actual domain or IP address
const char* API_DOMAIN = "194.164.59.137";

// API endpoints
const char* API_ENDPOINT = "/api/device/capture/";

// Device serial number - will be auto-generated from MAC if empty
const char* DEVICE_SERIAL = "";

// SSL/TLS Configuration
const char* rootCACertificate = NULL;
bool validateSSL = false;

// Deep sleep duration: 2 hours = 7200 seconds = 7200000000 microseconds
const unsigned long DEEP_SLEEP_DURATION_US = 7200000000ULL; // 2 hours

// ============================================================================
// PIN DEFINITIONS
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

// LED Status pin (built-in LED on ESP32-CAM)
#define LED_STATUS_PIN    4

// Battery monitoring pin (optional)
#define BATTERY_ADC_PIN   14

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

Preferences preferences;
String serialNumber = "";
String wifiSSID = "";
String wifiPassword = "";

// AP Mode
const char* apSSID = "SmartCamera-SETUP";
const char* apPassword = "";
AsyncWebServer server(80);
bool apMode = false;

bool cameraInitialized = false;
float batteryVoltage = 0.0;
const float BATTERY_LOW_THRESHOLD = 3.3;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

String getDeviceSerial() {
  if (strlen(DEVICE_SERIAL) > 0) {
    return String(DEVICE_SERIAL);
  }
  
  uint8_t mac[6];
  esp_read_mac(mac, ESP_MAC_WIFI_STA);
  char serial[10];
  sprintf(serial, "ESP-%02X%02X%02X", mac[3], mac[4], mac[5]);
  return String(serial);
}

String buildApiUrl(const char* endpoint) {
  String url;
  bool isIP = true;
  for (int i = 0; API_DOMAIN[i] != '\0'; i++) {
    char c = API_DOMAIN[i];
    if ((c < '0' || c > '9') && c != '.') {
      isIP = false;
      break;
    }
  }
  
  if (isIP) {
    url = "http://";
    url += String(API_DOMAIN);
    url += ":8000";
  } else {
    url = "https://";
    url += String(API_DOMAIN);
  }
  
  if (endpoint[0] != '/') {
    url += "/";
  }
  url += endpoint;
  return url;
}

bool isIPAddress(const char* domain) {
  for (int i = 0; domain[i] != '\0'; i++) {
    char c = domain[i];
    if ((c < '0' || c > '9') && c != '.') {
      return false;
    }
  }
  return true;
}

void configureSSLClient(WiFiClientSecure& client) {
  if (isIPAddress(API_DOMAIN)) {
    return;
  }
  
  if (validateSSL && rootCACertificate) {
    client.setCACert(rootCACertificate);
  } else {
    client.setInsecure();
  }
  client.setTimeout(10);
}

float readBatteryVoltage() {
  int adcValue = analogRead(BATTERY_ADC_PIN);
  float voltage = (adcValue / 4095.0) * 3.3 * 2.0; // Assuming 2:1 voltage divider
  return voltage;
}

// ============================================================================
// CAMERA FUNCTIONS
// ============================================================================

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
    Serial.printf("Camera init failed with error 0x%x\n", err);
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

String takePhoto() {
  if (!cameraInitialized) {
    Serial.println("Camera not initialized!");
    return "";
  }
  
  Serial.println("Capturing photo...");
  
  // Disable flash LED to save power
  digitalWrite(LED_STATUS_PIN, LOW);
  
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

// ============================================================================
// WIFI FUNCTIONS
// ============================================================================

bool loadWiFiCredentials() {
  preferences.begin("wifi", true);
  wifiSSID = preferences.getString("ssid", "");
  wifiPassword = preferences.getString("password", "");
  preferences.end();
  
  return wifiSSID.length() > 0;
}

void saveWiFiCredentials(String ssid, String password) {
  preferences.begin("wifi", false);
  preferences.putString("ssid", ssid);
  preferences.putString("password", password);
  preferences.end();
  Serial.println("WiFi credentials saved to flash");
}

bool connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(wifiSSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifiSSID.c_str(), wifiPassword.c_str());
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    return true;
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
    return false;
  }
}

// ============================================================================
// UPLOAD FUNCTIONS
// ============================================================================

bool uploadPhoto(String base64Image, String triggerType) {
  if (base64Image.length() == 0) {
    Serial.println("Upload: Failed - Empty image data");
    return false;
  }
  
  if (apMode) {
    Serial.println("Upload: Failed - In AP mode");
    return false;
  }
  
  HTTPClient http;
  String url = buildApiUrl(API_ENDPOINT);
  
  Serial.print("Uploading photo to: ");
  Serial.println(url);
  Serial.print("Trigger type: ");
  Serial.println(triggerType);
  
  // Use HTTPS for domains, HTTP for IP addresses
  if (isIPAddress(API_DOMAIN)) {
    http.begin(url);
  } else {
    WiFiClientSecure client;
    configureSSLClient(client);
    http.begin(client, url);
  }
  
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(30000);
  
  // Create JSON payload with trigger_type
  DynamicJsonDocument doc(1024 * 100); // Large enough for base64 image
  doc["serial_number"] = serialNumber;
  doc["image"] = base64Image;
  doc["trigger_type"] = triggerType; // "automatic" or "manual"
  doc["battery_voltage"] = batteryVoltage;
  doc["timestamp"] = millis();
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  int httpResponseCode = http.POST(jsonPayload);
  
  bool success = false;
  if (httpResponseCode > 0 && httpResponseCode < 400) {
    Serial.println("Upload: Success");
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    success = true;
  } else {
    Serial.println("Upload: Failed");
    Serial.print("HTTP Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
  return success;
}

// ============================================================================
// DEEP SLEEP FUNCTIONS
// ============================================================================

void enterDeepSleep() {
  Serial.println("Preparing for deep sleep...");
  
  // Read final battery status
  batteryVoltage = readBatteryVoltage();
  Serial.printf("Battery voltage: %.2fV\n", batteryVoltage);
  
  if (batteryVoltage < BATTERY_LOW_THRESHOLD) {
    Serial.println("WARNING: Low battery voltage!");
  }
  
  // Disable WiFi to save power
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
  
  // Turn off LED
  digitalWrite(LED_STATUS_PIN, LOW);
  
  // Configure wake-up source: Timer (2 hours)
  esp_sleep_enable_timer_wakeup(DEEP_SLEEP_DURATION_US);
  
  Serial.println("Entering deep sleep for 2 hours...");
  Serial.flush();
  delay(100);
  
  // Enter deep sleep
  esp_deep_sleep_start();
  // Code never reaches here
}

// ============================================================================
// AP MODE SETUP (for WiFi configuration)
// ============================================================================

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

void setupAPMode() {
  Serial.println("Setting up Access Point mode for initial configuration...");
  
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

// ============================================================================
// MAIN SETUP FUNCTION
// ============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Check wake-up reason
  esp_sleep_wakeup_cause_t wakeupReason = esp_sleep_get_wakeup_cause();
  
  Serial.println("ESP32-CAM Smart Mailbox - Timer Based");
  Serial.println("=====================================");
  
  switch(wakeupReason) {
    case ESP_SLEEP_WAKEUP_TIMER:
      Serial.println("Wake reason: Timer (automatic - 2 hour interval)");
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
  
  // Get device serial number
  serialNumber = getDeviceSerial();
  Serial.print("Device Serial: ");
  Serial.println(serialNumber);
  
  // Initialize LED
  pinMode(LED_STATUS_PIN, OUTPUT);
  digitalWrite(LED_STATUS_PIN, LOW);
  
  // Initialize battery monitoring (optional)
  pinMode(BATTERY_ADC_PIN, INPUT);
  analogSetAttenuation(ADC_11db);
  batteryVoltage = readBatteryVoltage();
  Serial.printf("Battery voltage: %.2fV\n", batteryVoltage);
  
  if (batteryVoltage < BATTERY_LOW_THRESHOLD) {
    Serial.println("WARNING: Low battery voltage!");
  }
  
  // Initialize camera
  Serial.println("Initializing camera...");
  cameraInitialized = initCamera();
  
  if (!cameraInitialized) {
    Serial.println("ERROR: Camera initialization failed!");
    delay(5000);
    enterDeepSleep();
    return;
  }
  
  // Load WiFi credentials
  if (loadWiFiCredentials()) {
    Serial.println("WiFi credentials found, connecting...");
    if (!connectToWiFi()) {
      Serial.println("WiFi connection failed! Entering AP mode...");
      setupAPMode();
      // In AP mode, we can't upload, so just wait and sleep
      delay(30000); // Wait 30 seconds for setup
      enterDeepSleep();
      return;
    }
  } else {
    Serial.println("No WiFi credentials found - Starting setup mode...");
    setupAPMode();
    delay(30000); // Wait 30 seconds for setup
    enterDeepSleep();
    return;
  }
  
  // Determine trigger type based on wake reason
  String triggerType = "automatic";
  if (wakeupReason == ESP_SLEEP_WAKEUP_EXT0) {
    triggerType = "manual";
  }
  
  // Capture and upload photo
  Serial.println("Starting capture cycle...");
  String base64Image = takePhoto();
  
  if (base64Image.length() == 0) {
    Serial.println("ERROR: Photo capture failed!");
    delay(5000);
    enterDeepSleep();
    return;
  }
  
  Serial.printf("Photo captured: %d bytes (base64: %d chars)\n", 
                 base64Image.length() * 3 / 4, base64Image.length());
  
  // Upload to server
  bool success = uploadPhoto(base64Image, triggerType);
  
  if (success) {
    Serial.println("Photo uploaded successfully!");
  } else {
    Serial.println("ERROR: Photo upload failed!");
  }
  
  // Return to deep sleep
  Serial.println("Cycle complete. Returning to sleep...");
  delay(1000); // Allow serial to flush
  enterDeepSleep();
}

// ============================================================================
// MAIN LOOP FUNCTION
// ============================================================================

void loop() {
  // This should never be reached
  // Device enters deep sleep in setup()
  // If we somehow get here, enter sleep immediately
  delay(1000);
  enterDeepSleep();
}

