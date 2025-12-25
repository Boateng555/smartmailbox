# ESP32-CAM Smart Mailbox Camera - Hardware Testing Procedure

## Overview
This document provides step-by-step testing procedures to verify all hardware components are correctly wired and functioning.

## Prerequisites

### Required Tools
- USB-to-Serial adapter (FTDI or CP2102)
- Multimeter
- Logic analyzer or oscilloscope (optional, for debugging)
- Serial monitor (Arduino IDE or PlatformIO)
- Test jumper wires
- Breadboard (for initial testing)

### Required Software
- PlatformIO or Arduino IDE
- Serial monitor (115200 baud)
- AT command terminal (for A7670 testing)

## Pre-Testing Setup

### 1. Connect Serial Monitor
```
USB-to-Serial Adapter:
├── TX → ESP32 GPIO 1 (UART0 TX)
├── RX → ESP32 GPIO 3 (UART0 RX)
├── GND → ESP32 GND
└── 5V → ESP32 5V (or use 3.3V if available)

Note: Disconnect GPIO 0 from anything during programming
```

### 2. Flash Test Firmware
1. Open project in PlatformIO
2. Connect ESP32-CAM via USB-to-Serial
3. Hold BOOT button, press RESET, release BOOT
4. Upload firmware: `pio run -t upload`
5. Open serial monitor: `pio device monitor`

## Component Testing Procedures

### Test 1: ESP32-CAM Basic Functionality

**Objective:** Verify ESP32-CAM boots and serial communication works.

**Steps:**
1. Power on ESP32-CAM (via USB or battery)
2. Open serial monitor (115200 baud)
3. Look for boot messages:
   ```
   ESP32-CAM Smart Camera Firmware
   ====================
   Device powered on - Initializing...
   ```

**Expected Results:**
- Serial output appears immediately
- No boot loops or crashes
- Device serial number is displayed

**Troubleshooting:**
- No output: Check serial connections, baud rate
- Boot loops: Check power supply, GPIO 0 state
- Crashes: Check for short circuits

---

### Test 2: Camera Module

**Objective:** Verify camera initializes and can capture images.

**Steps:**
1. Ensure camera module is properly connected (built-in on ESP32-CAM)
2. Monitor serial output for:
   ```
   Initializing camera...
   Camera initialized successfully!
   ```
3. Send test command via serial: `capture`
4. Check for image capture confirmation

**Expected Results:**
- Camera initialization succeeds
- No error codes
- Image capture works

**Troubleshooting:**
- Camera init failed: Check camera module connection
- Error 0x20001: PSRAM issue, check board configuration
- No image: Check camera power, verify pin connections

---

### Test 3: A7670 4G Module - Power Control

**Objective:** Verify A7670 module powers on correctly.

**Hardware Check:**
1. Verify connections:
   - GPIO 33 → A7670 PWR_KEY
   - GPIO 16 → A7670 TX (ESP32 RX)
   - GPIO 17 → A7670 RX (ESP32 TX)
   - 5V → A7670 VCC (via regulator)
   - GND → Common ground

2. Measure voltages:
   - A7670 VCC: Should be 3.8V (typical)
   - PWR_KEY: Should be LOW normally, HIGH for 1s to boot

**Software Test:**
1. Monitor serial output
2. Look for A7670 initialization:
   ```
   Initializing A7670 cellular module...
   A7670 powered on
   Waiting for module to boot...
   ```

**Expected Results:**
- A7670 powers on within 5 seconds
- No power supply issues
- Module responds after boot

**Troubleshooting:**
- Module doesn't power on: Check PWR_KEY connection, verify 5V supply
- Power supply drops: Add larger capacitor, check regulator capacity
- Module doesn't boot: Check power timing, verify connections

---

### Test 4: A7670 4G Module - UART Communication

**Objective:** Verify AT command communication with A7670.

**Steps:**
1. After A7670 boots, firmware should send AT commands
2. Monitor serial output for:
   ```
   Sending: AT
   Response: OK
   ```
3. Test manually via serial monitor:
   - Type commands to test AT interface
   - Check responses

**Expected Results:**
- AT commands return "OK"
- UART communication is stable
- No data corruption

**Troubleshooting:**
- No response: Check TX/RX connections (may be swapped)
- Garbled output: Check baud rate (should be 115200)
- Timeout: Check power supply, module may not be fully booted

---

### Test 5: A7670 4G Module - Network Registration

**Objective:** Verify A7670 can register on cellular network.

**Steps:**
1. Insert SIM card (with data plan)
2. Monitor serial output for network registration:
   ```
   Checking network registration...
   Network registered: Yes
   Signal strength: -85 dBm
   ```
3. Wait for GPRS registration:
   ```
   Checking GPRS registration...
   GPRS registered: Yes
   ```

**Expected Results:**
- Network registration succeeds (may take 30-60 seconds)
- Signal strength is readable
- GPRS registration completes

**Troubleshooting:**
- No network: Check SIM card, verify APN settings
- Weak signal: Check antenna connection, location
- Registration timeout: Check carrier compatibility, APN

---

### Test 6: A7670 4G Module - Data Connection

**Objective:** Verify PPP connection and internet access.

**Steps:**
1. After GPRS registration, firmware attempts PPP connection
2. Monitor for:
   ```
   Establishing PPP connection...
   PPP connected
   IP Address: 10.x.x.x
   ```
3. Test connectivity:
   ```
   Testing ping to 8.8.8.8...
   Ping successful
   ```

**Expected Results:**
- PPP connection establishes
- IP address is assigned
- Internet connectivity works

**Troubleshooting:**
- PPP fails: Check APN settings, carrier restrictions
- No IP: Check data plan, verify APN credentials
- No internet: Check firewall, carrier restrictions

---

### Test 7: IR Sensor

**Objective:** Verify IR sensor detects motion correctly.

**Hardware Check:**
1. Verify connections:
   - GPIO 13 → IR sensor OUT
   - 3.3V → IR sensor VCC
   - GND → IR sensor GND
   - (Optional) GPIO 2 → MOSFET gate for power control

2. Measure voltages:
   - IR sensor VCC: 3.3V
   - IR sensor OUT: LOW when no motion, HIGH when motion detected

**Software Test:**
1. Monitor serial output
2. Wave hand in front of sensor
3. Look for:
   ```
   IR sensor trigger detected!
   First trigger at: [timestamp]
   Second trigger at: [timestamp]
   Mail detected!
   ```

**Expected Results:**
- Sensor triggers on motion
- False positives are filtered (requires 2 triggers)
- Deep sleep wake-up works

**Troubleshooting:**
- No trigger: Check connections, verify sensor power
- False triggers: Adjust sensitivity, add focusing lens
- Always HIGH: Check sensor mode (should be single trigger)

---

### Test 8: Reed Switch

**Objective:** Verify door state detection.

**Hardware Check:**
1. Verify connections:
   - GPIO 12 → One terminal of reed switch
   - GND → Other terminal of reed switch
   - Internal pull-up enabled

2. Test with magnet:
   - Magnet near: GPIO 12 should read LOW (door closed)
   - Magnet away: GPIO 12 should read HIGH (door open)

**Software Test:**
1. Monitor serial output:
   ```
   Reed switch initialized on GPIO 12 - Door: CLOSED
   ```
2. Move magnet away:
   ```
   Door state changed: OPEN
   ```
3. Move magnet near:
   ```
   Door state changed: CLOSED
   ```

**Expected Results:**
- Door state reads correctly
- State changes are detected
- No bouncing or false readings

**Troubleshooting:**
- Always HIGH: Check magnet position, verify switch
- Always LOW: Check connections, verify pull-up
- Bouncing: Add debounce in software (already implemented)

---

### Test 9: Light Sensor

**Objective:** Verify ambient light detection.

**Hardware Check:**
1. Verify connections:
   - GPIO 14 → Light sensor (via voltage divider if LDR)
   - GND → Common ground
   - 3.3V → Pull-up (if needed)

2. Measure ADC:
   - Cover sensor: ADC should be low (< 100)
   - Expose to light: ADC should be high (> 100)

**Software Test:**
1. Monitor serial output:
   ```
   Light sensor initialized - Level: 450, Daytime: Yes
   ```
2. Cover sensor:
   ```
   Light level: 50, Daytime: No
   ```

**Expected Results:**
- Light level reads correctly
- Day/night detection works
- Values change with ambient light

**Troubleshooting:**
- Always 0: Check connections, verify sensor
- Always 4095: Check voltage divider, verify connections
- No change: Check sensor type, verify circuit

---

### Test 10: Battery Monitoring

**Objective:** Verify battery voltage reading.

**Hardware Check:**
1. Verify voltage divider:
   - Battery + → 10kΩ → GPIO 14 → 10kΩ → GND
   - Measure voltage at GPIO 14: Should be battery_voltage / 2

2. Test with multimeter:
   - Measure actual battery voltage
   - Compare with firmware reading

**Software Test:**
1. Monitor serial output:
   ```
   Battery monitoring initialized - Voltage: 3.85V
   Battery level OK - Device ready for operation
   ```
2. Check low battery warning:
   ```
   WARNING: Low battery voltage detected!
   ```

**Expected Results:**
- Voltage reading is accurate (±0.1V)
- Low battery warning triggers at correct threshold
- Reading updates regularly

**Troubleshooting:**
- Wrong reading: Check voltage divider resistors, verify values
- Always 0: Check connections, verify ADC pin
- Always max: Check voltage divider, verify battery connection

---

### Test 11: LED Status Indicator

**Objective:** Verify status LED works.

**Hardware Check:**
1. GPIO 4 is built-in flash LED on ESP32-CAM
2. No external wiring needed (unless using external LED)

**Software Test:**
1. Monitor LED behavior:
   - Fast blink: WiFi connecting
   - Slow blink: WiFi connected
   - Solid: Error state
   - Off: Deep sleep

**Expected Results:**
- LED blinks during initialization
- LED indicates connection status
- LED turns off during deep sleep

**Troubleshooting:**
- LED doesn't blink: Check GPIO 4, verify LED connection
- Always on: Check firmware, verify pin mode
- Always off: Check LED, verify power

---

### Test 12: Power Management

**Objective:** Verify power consumption and deep sleep.

**Hardware Check:**
1. Measure current consumption:
   - Active mode: ~200-250mA
   - Deep sleep: ~10-50µA (depending on wake sources)

2. Test with multimeter in series with battery

**Software Test:**
1. Monitor serial output for sleep messages:
   ```
   Entering deep sleep... (Wake on IR sensor GPIO 13 or timer)
   ```
2. Verify device wakes on:
   - IR sensor trigger
   - Timer expiration
   - Manual reset

**Expected Results:**
- Current drops to < 50µA in deep sleep
- Device wakes correctly
- Battery life is acceptable

**Troubleshooting:**
- High sleep current: Check for power leaks, disable unnecessary components
- Doesn't wake: Check wake source configuration
- Battery drains quickly: Check power consumption, verify deep sleep

---

## Integration Testing

### Test 13: Complete System Test

**Objective:** Verify all components work together.

**Steps:**
1. Power on device
2. Verify all components initialize
3. Test mail detection:
   - Trigger IR sensor
   - Verify camera captures photos
   - Verify photos upload to server
4. Test connectivity:
   - Verify cellular connection
   - Verify data upload
   - Verify heartbeat messages
5. Test power management:
   - Verify deep sleep
   - Verify wake on trigger
   - Monitor battery level

**Expected Results:**
- All components work together
- Mail detection triggers photo capture
- Photos upload successfully
- System enters deep sleep
- Battery monitoring works

---

## Test Results Template

```
Hardware Testing Results
=======================

Date: _______________
Tester: _______________

Component              Status    Notes
--------               ------    -----
ESP32-CAM Boot         [ ] PASS  [ ] FAIL
Camera Module          [ ] PASS  [ ] FAIL
A7670 Power            [ ] PASS  [ ] FAIL
A7670 UART             [ ] PASS  [ ] FAIL
A7670 Network          [ ] PASS  [ ] FAIL
A7670 Data             [ ] PASS  [ ] FAIL
IR Sensor              [ ] PASS  [ ] FAIL
Reed Switch            [ ] PASS  [ ] FAIL
Light Sensor           [ ] PASS  [ ] FAIL
Battery Monitoring     [ ] PASS  [ ] FAIL
LED Status             [ ] PASS  [ ] FAIL
Power Management       [ ] PASS  [ ] FAIL
System Integration     [ ] PASS  [ ] FAIL

Overall Status: [ ] READY  [ ] NEEDS WORK

Issues Found:
1. _______________________________________
2. _______________________________________
3. _______________________________________

Next Steps:
_________________________________________
_________________________________________
```

---

## Quick Test Commands

Via Serial Monitor, you can use these commands:

- `help` - Show available commands
- `status` - Show system status
- `capture` - Capture test photo
- `test_ir` - Test IR sensor
- `test_reed` - Test reed switch
- `test_light` - Test light sensor
- `test_battery` - Test battery monitoring
- `test_cellular` - Test cellular connection
- `reset` - Reset device

---

## Next Steps

After all tests pass:
1. Review test results
2. Fix any issues found
3. Perform final assembly
4. Deploy to mailbox
5. Monitor for 24-48 hours
6. Verify remote functionality


