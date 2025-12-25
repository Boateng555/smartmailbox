# How to Upload Firmware to ESP32-CAM

## Quick Start Guide

### Method 1: Using PlatformIO (Recommended)

#### Step 1: Install PlatformIO

**Option A: PlatformIO IDE (VS Code Extension)**
1. Install [VS Code](https://code.visualstudio.com/)
2. Open VS Code
3. Go to Extensions (Ctrl+Shift+X)
4. Search for "PlatformIO IDE"
5. Click Install

**Option B: PlatformIO Core (Command Line)**
```bash
pip install platformio
```

#### Step 2: Connect ESP32-CAM

**Hardware Connection:**
```
USB-to-Serial Adapter (FTDI/CP2102):
├── TX → ESP32 GPIO 1 (UART0 TX)
├── RX → ESP32 GPIO 3 (UART0 RX)
├── GND → ESP32 GND
└── 5V → ESP32 5V

IMPORTANT: GPIO 0 must be LOW during upload!
- Connect GPIO 0 to GND during upload
- Or use a button to pull GPIO 0 LOW
```

**Upload Sequence:**
1. Hold BOOT button (or connect GPIO 0 to GND)
2. Press and release RESET button
3. Release BOOT button
4. Upload firmware

#### Step 3: Navigate to Project

```bash
cd C:\esp32-cam-product\esp32-firmware
```

#### Step 4: Upload Firmware

**Using PlatformIO IDE (VS Code):**
1. Open the `esp32-firmware` folder in VS Code
2. Click the PlatformIO icon in the sidebar
3. Click "Upload" button (→) in the toolbar
4. Wait for upload to complete

**Using Command Line:**
```bash
# Navigate to firmware directory
cd esp32-firmware

# Upload firmware
pio run -t upload

# Or use PlatformIO Core
platformio run -t upload
```

#### Step 5: Monitor Serial Output

**Using PlatformIO IDE:**
1. Click "Monitor" button (plug icon) in toolbar
2. Or use: `pio device monitor`

**Using Command Line:**
```bash
pio device monitor
# Or
platformio device monitor
```

**Serial Monitor Settings:**
- Baud Rate: 115200
- Line Ending: Both NL & CR

### Method 2: Using Arduino IDE

#### Step 1: Install Arduino IDE
1. Download from [arduino.cc](https://www.arduino.cc/en/software)
2. Install Arduino IDE

#### Step 2: Install ESP32 Board Support
1. Open Arduino IDE
2. Go to File → Preferences
3. Add to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to Tools → Board → Boards Manager
5. Search for "ESP32"
6. Install "esp32 by Espressif Systems"

#### Step 3: Configure Board
1. Go to Tools → Board → ESP32 Arduino
2. Select "AI Thinker ESP32-CAM"
3. Set Upload Speed: 921600
4. Set Port: Select your USB-to-Serial port

#### Step 4: Upload
1. Open `src/main.cpp` in Arduino IDE
2. Hold BOOT button
3. Press RESET button
4. Release BOOT button
5. Click Upload button (→)
6. Wait for upload to complete

## Complete Upload Process

### 1. Prepare ESP32-CAM

**Before Upload:**
- Connect USB-to-Serial adapter
- Ensure GPIO 0 is connected to GND (or use BOOT button)
- Power on ESP32-CAM (5V)

### 2. Enter Download Mode

**Manual Method:**
1. Hold BOOT button
2. Press and release RESET button
3. Release BOOT button
4. ESP32 is now in download mode

**Automatic Method (if supported):**
- Some USB-to-Serial adapters auto-enter download mode
- Check adapter documentation

### 3. Upload Firmware

**PlatformIO:**
```bash
cd esp32-firmware
pio run -t upload
```

**Arduino IDE:**
- Click Upload button
- Wait for "Hard resetting via RTS pin..." message

### 4. Verify Upload

**Check Serial Monitor:**
```
ESP32-CAM Smart Mailbox - Timer Based
=====================================
Wake reason: Power on / Reset
Device Serial: ESP-12345
...
```

## Configuration Before Upload

### Update API Domain

Edit `src/main.cpp` and change:
```cpp
const char* API_DOMAIN = "194.164.59.137";  // Server IP address
```

Or for localhost testing:
```cpp
const char* API_DOMAIN = "192.168.1.100";  // Your computer's local IP
```

### Find Your Local IP

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your network adapter
```

**Mac/Linux:**
```bash
ifconfig
# Or
ip addr
# Look for inet address
```

## Troubleshooting

### Upload Fails: "Failed to connect to ESP32"

**Solutions:**
1. **Check GPIO 0**: Must be LOW during upload
   - Connect GPIO 0 to GND
   - Or hold BOOT button during upload

2. **Check USB-to-Serial Connection:**
   - Verify TX/RX are connected correctly
   - TX on adapter → RX on ESP32 (GPIO 3)
   - RX on adapter → TX on ESP32 (GPIO 1)

3. **Check Port:**
   - Verify correct COM port selected
   - Windows: Device Manager → Ports (COM & LPT)
   - Mac/Linux: `ls /dev/tty.*` or `ls /dev/ttyUSB*`

4. **Try Lower Upload Speed:**
   - Edit `platformio.ini`
   - Change `upload_speed = 921600` to `upload_speed = 115200`

5. **Check Drivers:**
   - Install USB-to-Serial drivers (CP2102, CH340, FTDI)
   - Download from manufacturer website

### Upload Fails: "Timed out waiting for packet header"

**Solutions:**
1. Hold BOOT button longer
2. Try different USB cable
3. Lower upload speed
4. Check power supply (use external 5V if needed)

### Device Not Found After Upload

**Solutions:**
1. Press RESET button
2. Check serial monitor (115200 baud)
3. Verify firmware uploaded successfully
4. Check for error messages in serial output

### Serial Monitor Shows Garbage

**Solutions:**
1. Check baud rate: Must be 115200
2. Close and reopen serial monitor
3. Press RESET button on ESP32
4. Verify TX/RX connections

## PlatformIO Commands Reference

```bash
# Build firmware (compile only)
pio run

# Upload firmware
pio run -t upload

# Monitor serial output
pio device monitor

# Clean build files
pio run -t clean

# Upload and monitor (combined)
pio run -t upload && pio device monitor

# List connected devices
pio device list
```

## Arduino IDE Settings

**Board Settings:**
- Board: "AI Thinker ESP32-CAM"
- Upload Speed: 921600
- CPU Frequency: 240MHz
- Flash Frequency: 80MHz
- Flash Mode: QIO
- Flash Size: 4MB (32Mb)
- Partition Scheme: Default 4MB with spiffs
- Core Debug Level: None
- Port: [Your COM port]

## Testing After Upload

### 1. Check Serial Output

Open serial monitor (115200 baud) and look for:
```
ESP32-CAM Smart Mailbox - Timer Based
=====================================
Wake reason: Power on / Reset
Device Serial: ESP-12345
Battery voltage: 3.85V
Initializing camera...
Camera initialized successfully!
```

### 2. Test WiFi Connection

If WiFi credentials are saved:
```
WiFi credentials found, connecting...
WiFi connected!
IP address: 192.168.1.100
```

If no WiFi credentials:
```
No WiFi credentials found - Starting setup mode...
SETUP MODE ACTIVE
WiFi Network Name: SmartCamera-SETUP
Setup Page: http://192.168.4.1/config
```

### 3. Test Photo Capture

Device should:
1. Wake every 2 hours automatically
2. Capture photo
3. Upload to server
4. Return to deep sleep

## WiFi Setup (First Time)

### Method 1: Web Interface

1. Device creates WiFi network: `SmartCamera-SETUP`
2. Connect your phone/computer to this network
3. Open browser: `http://192.168.4.1/config`
4. Enter your WiFi credentials
5. Device reboots and connects

### Method 2: Serial Commands (Future)

Can be added to firmware for serial-based WiFi setup.

## File Structure

```
esp32-firmware/
├── platformio.ini          # PlatformIO configuration
├── src/
│   ├── main.cpp           # Main firmware code
│   ├── a7670_cellular.h   # Cellular module header
│   └── a7670_cellular.cpp # Cellular module implementation
└── UPLOAD_FIRMWARE_GUIDE.md  # This file
```

## Next Steps After Upload

1. **Verify Upload**: Check serial monitor for boot messages
2. **Configure WiFi**: Use web interface or serial commands
3. **Test Camera**: Device should capture photos
4. **Test Upload**: Photos should upload to server
5. **Monitor Battery**: Check battery voltage in serial output

## Quick Reference

### Upload Checklist
- [ ] USB-to-Serial adapter connected
- [ ] GPIO 0 connected to GND (or BOOT button ready)
- [ ] ESP32-CAM powered on (5V)
- [ ] Correct COM port selected
- [ ] PlatformIO/Arduino IDE ready
- [ ] API_DOMAIN configured in code

### After Upload
- [ ] Serial monitor shows boot messages
- [ ] Camera initializes successfully
- [ ] WiFi connects (or setup mode works)
- [ ] Device enters deep sleep
- [ ] Device wakes every 2 hours

## Support

If you encounter issues:
1. Check serial monitor for error messages
2. Verify all connections
3. Try lower upload speed
4. Check PlatformIO/Arduino IDE version
5. Verify ESP32 board support is installed

## Notes

- **GPIO 0**: Must be LOW during upload (connect to GND or use BOOT button)
- **Upload Speed**: 921600 is fast but may need to lower to 115200 if issues
- **Serial Monitor**: Use 115200 baud rate
- **Deep Sleep**: Device sleeps for 2 hours between captures
- **First Boot**: Device may take longer to boot (WiFi setup mode)

