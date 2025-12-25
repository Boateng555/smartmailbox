# Server IP Address Configuration

## Server IP: `194.164.59.137`

This document lists all locations where the server IP address is configured.

## ✅ Already Configured

### 1. ESP32 Firmware
**File:** `esp32-firmware/src/main.cpp`
**Line:** 17
```cpp
const char* API_DOMAIN = "194.164.59.137";
```
**Status:** ✅ Correct

### 2. Deployment Documentation
**Files:**
- `deployment/FIRST_TIME_SETUP.md` - Uses `194.164.59.137`
- `deployment/INSTALL_STEP_BY_STEP.md` - Uses `194.164.59.137`
- `deployment/SERVER_SETUP_GUIDE.md` - Uses `194.164.59.137`
**Status:** ✅ Correct

### 3. Firmware Documentation
**Files:**
- `esp32-firmware/FIRMWARE_CHANGES.md` - Example shows `194.164.59.137`
- `esp32-firmware/QUICK_UPLOAD.md` - Updated to show `194.164.59.137`
- `esp32-firmware/UPLOAD_FIRMWARE_GUIDE.md` - Updated to show `194.164.59.137`
**Status:** ✅ Correct

## Configuration Locations

### ESP32-CAM Firmware
- **File:** `esp32-firmware/src/main.cpp`
- **Variable:** `API_DOMAIN`
- **Value:** `"194.164.59.137"`
- **Port:** `8000` (added automatically for IP addresses)

### Django Settings (Production)
- **File:** `django-webapp/iot_platform/settings_production.py`
- **Variable:** `API_DOMAIN` (from environment)
- **Environment Variable:** `API_DOMAIN=194.164.59.137`

### Django Settings (Development)
- **File:** `django-webapp/iot_platform/settings.py`
- **ALLOWED_HOSTS:** `*` (allows all hosts in development)
- **For Production:** Set `ALLOWED_HOSTS=194.164.59.137`

### Nginx Configuration
- **File:** `nginx/conf.d/iot_platform.conf`
- **Server Name:** `_` (accepts all)
- **Proxy Pass:** `http://web:8001` (internal Docker network)

### Docker Compose
- **File:** `docker-compose.yml`
- **Ports:** 
  - `8000:8001` (external:internal)
  - `80:80` (HTTP)
  - `443:443` (HTTPS)

## API Endpoints

All endpoints use the server IP `194.164.59.137`:

### ESP32 Device Endpoints
- **Capture:** `http://194.164.59.137:8000/api/device/capture/`
- **Heartbeat:** `http://194.164.59.137:8000/api/device/heartbeat/`
- **Trigger:** `http://194.164.59.137:8000/api/device/trigger/`
- **Status:** `http://194.164.59.137:8000/api/device/status/`

### Web Interface
- **Home:** `http://194.164.59.137/`
- **Admin:** `http://194.164.59.137/admin/`
- **Dashboard:** `http://194.164.59.137/dashboard/`

## Environment Variables

### Production Server
Set these environment variables on your server:

```bash
ALLOWED_HOSTS=194.164.59.137
API_DOMAIN=194.164.59.137
```

### Docker Environment
In `.env` file or docker-compose environment:
```bash
ALLOWED_HOSTS=194.164.59.137
API_DOMAIN=194.164.59.137
```

## Testing

### Test from ESP32
ESP32 will connect to:
```
http://194.164.59.137:8000/api/device/capture/
```

### Test from Browser
- **Web Interface:** `http://194.164.59.137`
- **API Direct:** `http://194.164.59.137:8000/api/device/capture/`

### Test with curl
```bash
curl -X POST http://194.164.59.137:8000/api/device/capture/ \
  -H "Content-Type: application/json" \
  -d '{"serial_number":"ESP-TEST","image":"base64..."}'
```

## Firewall Configuration

Ensure these ports are open on `194.164.59.137`:
- **Port 80** (HTTP)
- **Port 443** (HTTPS)
- **Port 8000** (Django direct access - optional)
- **Port 22** (SSH)

## DNS Configuration (Optional)

If you have a domain name:
1. Point domain to `194.164.59.137`
2. Update `ALLOWED_HOSTS` to include domain
3. Update ESP32 firmware to use domain instead of IP
4. Configure SSL certificates

## Summary

✅ **ESP32 Firmware:** Configured with `194.164.59.137`
✅ **Documentation:** All references updated
✅ **Deployment Scripts:** Use `194.164.59.137`
✅ **Ready to Deploy:** All configurations correct

The server IP `194.164.59.137` is now configured in all necessary locations.


