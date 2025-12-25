#ifndef A7670_CELLULAR_H
#define A7670_CELLULAR_H

#include <Arduino.h>
#include <HardwareSerial.h>

// A7670 4G Module Configuration
#define A7670_POWER_PIN      33  // GPIO 33 for power control (HIGH for 1s to boot) - Changed from GPIO 4 (conflict with LED)
#define A7670_RX_PIN         16  // UART RX (ESP32 receives from A7670)
#define A7670_TX_PIN         17  // UART TX (ESP32 sends to A7670)
#define A7670_BAUD           115200
#define A7670_UART_NUM       2   // Use UART2

// A7670 Power Control Timing
#define A7670_POWER_ON_TIME  1000  // Hold HIGH for 1 second
#define A7670_BOOT_TIME      5000  // Wait 5 seconds after power on

// Network Registration Timeouts
#define REGISTRATION_TIMEOUT 60000  // 60 seconds
#define PPP_CONNECT_TIMEOUT  30000  // 30 seconds

// APN Configuration (adjust per carrier)
#define CELLULAR_APN         "internet"
#define CELLULAR_USER        ""
#define CELLULAR_PASS        ""

class A7670Cellular {
private:
    HardwareSerial* serial;
    bool initialized;
    bool connected;
    String ipAddress;
    unsigned long lastCheck;
    
public:
    A7670Cellular();
    ~A7670Cellular();
    
    // Initialization
    bool begin();
    bool powerOn();
    bool powerOff();
    bool isInitialized() { return initialized; }
    
    // Connection Management
    bool connect();
    bool disconnect();
    bool isConnected() { return connected; }
    String getIPAddress() { return ipAddress; }
    
    // Network Status
    bool checkNetworkRegistration();
    bool checkGPRSRegistration();
    bool checkSignalStrength(int* rssi);
    
    // PPP Connection
    bool establishPPP();
    bool checkPPPStatus();
    
    // AT Commands
    String sendATCommand(String command, unsigned long timeout = 2000);
    bool waitForResponse(String expected, unsigned long timeout = 5000);
    
    // HTTP Client (over cellular)
    bool httpPost(String url, String payload, String& response);
    bool httpGet(String url, String& response);
    
    // Data Usage
    unsigned long getDataUsageBytes();
    void resetDataUsage();
    
    // Utilities
    bool ping(String host);
    void printStatus();
};

#endif






