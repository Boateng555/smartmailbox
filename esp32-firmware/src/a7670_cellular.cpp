#include "a7670_cellular.h"
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

A7670Cellular::A7670Cellular() {
    serial = new HardwareSerial(A7670_UART_NUM);
    initialized = false;
    connected = false;
    ipAddress = "";
    lastCheck = 0;
}

A7670Cellular::~A7670Cellular() {
    if (serial) {
        delete serial;
    }
}

bool A7670Cellular::begin() {
    Serial.println("Initializing A7670 cellular module...");
    
    // Initialize UART
    serial->begin(A7670_BAUD, SERIAL_8N1, A7670_RX_PIN, A7670_TX_PIN);
    delay(1000);
    
    // Power on module
    if (!powerOn()) {
        Serial.println("Failed to power on A7670");
        return false;
    }
    
    // Wait for module to boot
    delay(A7670_BOOT_TIME);
    
    // Test AT command
    String response = sendATCommand("AT", 3000);
    if (response.indexOf("OK") == -1) {
        Serial.println("A7670 not responding to AT commands");
        return false;
    }
    Serial.println("A7670 responding");
    
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
    String apnCmd = "AT+CGDCONT=1,\"IP\",\"" + String(CELLULAR_APN) + "\"";
    sendATCommand(apnCmd, 3000);
    
    initialized = true;
    Serial.println("A7670 initialized successfully");
    return true;
}

bool A7670Cellular::powerOn() {
    Serial.println("Powering on A7670...");
    pinMode(A7670_POWER_PIN, OUTPUT);
    digitalWrite(A7670_POWER_PIN, LOW);
    delay(100);
    digitalWrite(A7670_POWER_PIN, HIGH);
    delay(A7670_POWER_ON_TIME);
    digitalWrite(A7670_POWER_PIN, LOW);
    Serial.println("A7670 power sequence completed");
    return true;
}

bool A7670Cellular::powerOff() {
    Serial.println("Powering off A7670...");
    digitalWrite(A7670_POWER_PIN, LOW);
    connected = false;
    initialized = false;
    return true;
}

bool A7670Cellular::checkNetworkRegistration() {
    String response = sendATCommand("AT+CREG?", 5000);
    // Response format: +CREG: 0,1 or +CREG: 0,5
    // 1 = registered home network, 5 = registered roaming
    if (response.indexOf("0,1") != -1 || response.indexOf("0,5") != -1) {
        return true;
    }
    return false;
}

bool A7670Cellular::checkGPRSRegistration() {
    String response = sendATCommand("AT+CGREG?", 5000);
    // Response format: +CGREG: 0,1 or +CGREG: 0,5
    if (response.indexOf("0,1") != -1 || response.indexOf("0,5") != -1) {
        return true;
    }
    return false;
}

bool A7670Cellular::checkSignalStrength(int* rssi) {
    String response = sendATCommand("AT+CSQ", 3000);
    // Response format: +CSQ: 31,99
    // First number is signal strength (0-31, 99 = unknown)
    int index = response.indexOf("+CSQ:");
    if (index != -1) {
        int start = response.indexOf(" ", index) + 1;
        int end = response.indexOf(",", start);
        if (end == -1) end = response.indexOf("\r", start);
        String rssiStr = response.substring(start, end);
        *rssi = rssiStr.toInt();
        // Convert to dBm: -113 + (rssi * 2)
        *rssi = -113 + (*rssi * 2);
        return (*rssi > -113);
    }
    return false;
}

bool A7670Cellular::establishPPP() {
    Serial.println("Establishing PPP connection...");
    
    // Activate PDP context
    String response = sendATCommand("AT+CGACT=1,1", 10000);
    if (response.indexOf("OK") == -1) {
        Serial.println("Failed to activate PDP context");
        return false;
    }
    
    // Get IP address
    response = sendATCommand("AT+CGPADDR=1", 5000);
    int index = response.indexOf("+CGPADDR:");
    if (index != -1) {
        int start = response.indexOf("\"", index) + 1;
        int end = response.indexOf("\"", start);
        ipAddress = response.substring(start, end);
        Serial.print("Cellular IP: ");
        Serial.println(ipAddress);
    }
    
    // Note: A7670 uses AT commands for HTTP, not direct TCP/IP
    // For ESP32, we'll use the module's built-in HTTP client
    connected = true;
    return true;
}

bool A7670Cellular::checkPPPStatus() {
    String response = sendATCommand("AT+CGACT?", 3000);
    // Check if PDP context is active
    if (response.indexOf("1,1") != -1) {
        return true;
    }
    return false;
}

bool A7670Cellular::connect() {
    if (!initialized) {
        if (!begin()) {
            return false;
        }
    }
    
    // Check network registration
    unsigned long startTime = millis();
    while (!checkNetworkRegistration() && (millis() - startTime) < REGISTRATION_TIMEOUT) {
        Serial.println("Waiting for network registration...");
        delay(2000);
    }
    
    if (!checkNetworkRegistration()) {
        Serial.println("Network registration timeout");
        return false;
    }
    Serial.println("Network registered");
    
    // Check GPRS registration
    startTime = millis();
    while (!checkGPRSRegistration() && (millis() - startTime) < REGISTRATION_TIMEOUT) {
        Serial.println("Waiting for GPRS registration...");
        delay(2000);
    }
    
    if (!checkGPRSRegistration()) {
        Serial.println("GPRS registration timeout");
        return false;
    }
    Serial.println("GPRS registered");
    
    // Establish PPP connection
    if (!establishPPP()) {
        return false;
    }
    
    // Test connection with ping
    Serial.println("Testing connection...");
    if (ping("8.8.8.8")) {
        Serial.println("Cellular connection established and tested");
        return true;
    } else {
        Serial.println("Connection test failed");
        return false;
    }
}

bool A7670Cellular::disconnect() {
    sendATCommand("AT+CGACT=0,1", 5000);
    connected = false;
    ipAddress = "";
    return true;
}

String A7670Cellular::sendATCommand(String command, unsigned long timeout) {
    serial->print(command);
    serial->print("\r\n");
    
    unsigned long startTime = millis();
    String response = "";
    
    while (millis() - startTime < timeout) {
        if (serial->available()) {
            char c = serial->read();
            response += c;
            if (response.endsWith("OK\r\n") || response.endsWith("ERROR\r\n")) {
                break;
            }
        }
    }
    
    return response;
}

bool A7670Cellular::waitForResponse(String expected, unsigned long timeout) {
    unsigned long startTime = millis();
    String response = "";
    
    while (millis() - startTime < timeout) {
        if (serial->available()) {
            char c = serial->read();
            response += c;
            if (response.indexOf(expected) != -1) {
                return true;
            }
        }
    }
    
    return false;
}

bool A7670Cellular::httpPost(String url, String payload, String& response) {
    // A7670 HTTP POST using AT commands
    // Note: This is a simplified version - full implementation would handle SSL
    
    Serial.println("Sending HTTP POST via A7670...");
    
    // Initialize HTTP service
    sendATCommand("AT+HTTPINIT", 3000);
    
    // Set HTTP parameters
    String cmd = "AT+HTTPPARA=\"URL\",\"" + url + "\"";
    sendATCommand(cmd, 3000);
    
    // Set content type
    sendATCommand("AT+HTTPPARA=\"CONTENT\",\"application/json\"", 3000);
    
    // Set data
    cmd = "AT+HTTPDATA=" + String(payload.length()) + ",10000";
    sendATCommand(cmd, 3000);
    delay(100);
    serial->print(payload);
    delay(1000);
    
    // Send POST request
    String httpResponse = sendATCommand("AT+HTTPACTION=1", 30000);
    
    // Read response
    sendATCommand("AT+HTTPREAD", 5000);
    
    // Terminate HTTP service
    sendATCommand("AT+HTTPTERM", 3000);
    
    // Parse response code
    int codeIndex = httpResponse.indexOf("+HTTPACTION: 1,");
    if (codeIndex != -1) {
        int codeStart = httpResponse.indexOf(",", codeIndex) + 1;
        int codeEnd = httpResponse.indexOf(",", codeStart);
        String codeStr = httpResponse.substring(codeStart, codeEnd);
        int code = codeStr.toInt();
        
        if (code >= 200 && code < 300) {
            response = "Success";
            return true;
        }
    }
    
    return false;
}

bool A7670Cellular::httpGet(String url, String& response) {
    // Similar to httpPost but with GET method
    sendATCommand("AT+HTTPINIT", 3000);
    String cmd = "AT+HTTPPARA=\"URL\",\"" + url + "\"";
    sendATCommand(cmd, 3000);
    String httpResponse = sendATCommand("AT+HTTPACTION=0", 30000);
    sendATCommand("AT+HTTPTERM", 3000);
    
    // Parse response
    int codeIndex = httpResponse.indexOf("+HTTPACTION: 0,");
    if (codeIndex != -1) {
        int codeStart = httpResponse.indexOf(",", codeIndex) + 1;
        int codeEnd = httpResponse.indexOf(",", codeStart);
        String codeStr = httpResponse.substring(codeStart, codeEnd);
        int code = codeStr.toInt();
        
        if (code >= 200 && code < 300) {
            return true;
        }
    }
    
    return false;
}

bool A7670Cellular::ping(String host) {
    String cmd = "AT+SNPING4=\"" + host + "\",1,32,5000";
    String response = sendATCommand(cmd, 10000);
    return response.indexOf("OK") != -1;
}

void A7670Cellular::printStatus() {
    Serial.println("=== A7670 Status ===");
    Serial.print("Initialized: ");
    Serial.println(initialized ? "Yes" : "No");
    Serial.print("Connected: ");
    Serial.println(connected ? "Yes" : "No");
    Serial.print("IP Address: ");
    Serial.println(ipAddress.length() > 0 ? ipAddress : "None");
    
    int rssi = 0;
    if (checkSignalStrength(&rssi)) {
        Serial.print("Signal Strength: ");
        Serial.print(rssi);
        Serial.println(" dBm");
    }
}

unsigned long A7670Cellular::getDataUsageBytes() {
    // Get data usage from A7670 (if supported)
    String response = sendATCommand("AT+GDCNT?", 3000);
    // Parse response to get bytes
    // This is carrier/module dependent
    return 0;
}

void A7670Cellular::resetDataUsage() {
    sendATCommand("AT+GDCNT=0", 3000);
}







