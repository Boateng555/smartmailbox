# Quick Upload Guide - ESP32-CAM Firmware

## Fastest Way to Upload

### 1. Install PlatformIO (if not installed)

**VS Code Extension:**
- Open VS Code
- Install "PlatformIO IDE" extension

**Or Command Line:**
```bash
pip install platformio
```

### 2. Connect ESP32-CAM

```
USB-to-Serial Adapter:
TX → ESP32 GPIO 1
RX → ESP32 GPIO 3
GND → ESP32 GND
5V → ESP32 5V

IMPORTANT: GPIO 0 → GND (during upload)
```

### 3. Upload Firmware

**In VS Code (PlatformIO):**
1. Open `esp32-firmware` folder
2. Click Upload button (→) in PlatformIO toolbar

**Or Command Line:**
```bash
cd esp32-firmware
pio run -t upload
```

### 4. Enter Download Mode

**Before clicking Upload:**
1. Hold BOOT button (or connect GPIO 0 to GND)
2. Press RESET button
3. Release BOOT button
4. Click Upload

### 5. Monitor Output

```bash
pio device monitor
```

**Expected Output:**
```
ESP32-CAM Smart Mailbox - Timer Based
=====================================
Wake reason: Power on / Reset
Device Serial: ESP-XXXXXX
...
```

## Common Issues

### "Failed to connect"
- **Fix**: GPIO 0 must be LOW (connect to GND or hold BOOT)

### "Port not found"
- **Fix**: Check Device Manager for COM port, select correct port

### "Timed out"
- **Fix**: Lower upload speed in `platformio.ini` to 115200

## Configuration

**Edit `src/main.cpp` line 38:**
```cpp
const char* API_DOMAIN = "194.164.59.137";  // Server IP address
```

For localhost testing, use your computer's IP:
- Windows: `ipconfig` → IPv4 Address
- Example: `"192.168.1.100"`

## That's It!

After upload, device will:
- Wake every 2 hours
- Capture photo
- Upload to server
- Sleep again

