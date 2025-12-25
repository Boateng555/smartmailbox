# Complete Deployment Guide

## Overview
This guide covers the complete deployment process from GitHub to production server and ESP32-CAM setup.

## Step 1: Create GitHub Repository

### 1.1 Initialize Git (if not already done)
```bash
cd C:\esp32-cam-product
git init
```

### 1.2 Create .gitignore
Create `.gitignore` file in project root:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/
dist/
build/

# Django
*.log
*.pot
*.pyc
db.sqlite3
media/
staticfiles/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
*.env

# ESP32
.pio/
.vscode/
*.bin
*.elf

# OS
.DS_Store
Thumbs.db

# Secrets
secrets.json
firebase-key.json
```

### 1.3 Create GitHub Repository
1. Go to GitHub.com
2. Click "New repository"
3. Name: `esp32-cam-product` (or your choice)
4. Description: "Smart Mailbox System with ESP32-CAM"
5. Choose: Private or Public
6. **Don't** initialize with README (we already have files)
7. Click "Create repository"

### 1.4 Push to GitHub
```bash
cd C:\esp32-cam-product
git add .
git commit -m "Initial commit: Smart Mailbox System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/esp32-cam-product.git
git push -u origin main
```

## Step 2: Deploy to Linux Server

### 2.1 Server Requirements
- Ubuntu 20.04+ or Debian 11+
- Python 3.9+
- PostgreSQL or MySQL (recommended) or SQLite (for testing)
- Nginx (for reverse proxy)
- Supervisor or systemd (for process management)

### 2.2 Server Setup Commands

#### Connect to Server
```bash
ssh user@your-server-ip
```

#### Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install PostgreSQL (recommended)
sudo apt install postgresql postgresql-contrib -y

# Install Nginx
sudo apt install nginx -y

# Install Git
sudo apt install git -y

# Install Supervisor (for process management)
sudo apt install supervisor -y
```

#### Clone Repository
```bash
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/esp32-cam-product.git
sudo chown -R $USER:$USER esp32-cam-product
cd esp32-cam-product/django-webapp
```

#### Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment Variables
```bash
cd django-webapp
nano .env
```

Add these variables:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,194.164.59.137
DATABASE_URL=postgresql://user:password@localhost/dbname

# Firebase Vision API
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-key.json

# Email (SMTP or AWS SES)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Stripe (if using)
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Server IP
SERVER_IP=194.164.59.137
```

#### Database Setup
```bash
# If using PostgreSQL
sudo -u postgres psql
CREATE DATABASE mailbox_db;
CREATE USER mailbox_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mailbox_db TO mailbox_user;
\q

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

#### Setup Supervisor (Process Manager)
```bash
sudo nano /etc/supervisor/conf.d/mailbox.conf
```

Add:
```ini
[program:mailbox]
command=/var/www/esp32-cam-product/django-webapp/venv/bin/gunicorn iot_platform.wsgi:application --bind 127.0.0.1:8000 --workers 3
directory=/var/www/esp32-cam-product/django-webapp
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/mailbox.log
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mailbox
```

#### Setup Nginx (Reverse Proxy)
```bash
sudo nano /etc/nginx/sites-available/mailbox
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com 194.164.59.137;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/esp32-cam-product/django-webapp/staticfiles/;
    }

    location /media/ {
        alias /var/www/esp32-cam-product/django-webapp/media/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/mailbox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Setup SSL (Optional but Recommended)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Step 3: Upload ESP32-CAM Firmware

### 3.1 Update Server IP in Firmware
```bash
cd C:\esp32-cam-product\esp32-firmware\src
```

Edit `main.cpp` and ensure:
```cpp
const char* API_DOMAIN = "194.164.59.137";
```

### 3.2 Upload Firmware to ESP32-CAM

#### Option A: Using PlatformIO (Recommended)
```bash
cd C:\esp32-cam-product\esp32-firmware
pio run --target upload
```

#### Option B: Using Arduino IDE
1. Open `esp32-firmware/src/main.cpp` in Arduino IDE
2. Select board: ESP32 Wrover Module
3. Select partition scheme: Huge APP
4. Click Upload

### 3.3 Hardware Connections
- Connect ESP32-CAM to computer via USB
- Ensure proper drivers installed
- Put ESP32-CAM in upload mode (hold BOOT button, press RESET, release BOOT)

## Step 4: Testing Checklist

### 4.1 Server Testing
```bash
# Test Django server
curl http://194.164.59.137/

# Test API endpoint
curl http://194.164.59.137/api/device/heartbeat/

# Check logs
sudo tail -f /var/log/mailbox.log
```

### 4.2 ESP32-CAM Testing

#### Test 1: WiFi Connection
- ESP32 should connect to WiFi
- Check serial monitor for connection status

#### Test 2: Automatic Capture
- Wait 2 hours (or modify timer for testing)
- ESP32 should wake, capture photo, upload to server
- Check server logs for incoming request

#### Test 3: Manual Trigger
- Open web app: `http://194.164.59.137`
- Click "Check Mailbox" button
- ESP32 should capture on next wake cycle
- Verify capture appears in dashboard

#### Test 4: ChatGPT Analysis
- After capture uploads, check if analysis appears
- Verify mail detection works correctly

### 4.3 Full System Test

1. **ESP32 Wake Test**
   - Verify ESP32 wakes every 2 hours
   - Check battery usage is acceptable

2. **Photo Upload Test**
   - Verify photos upload successfully
   - Check image quality

3. **AI Analysis Test**
   - Verify ChatGPT Vision API analyzes images
   - Check detection accuracy

4. **Notification Test**
   - Verify notifications sent to app
   - Check email notifications (if configured)

5. **Click Limit Test**
   - Test free user limit (3 clicks/day)
   - Test premium user limit (10 clicks/day)

6. **Web App Test**
   - Login and view dashboard
   - Check mailbox button works
   - Verify captures display correctly

## Step 5: Monitoring & Maintenance

### 5.1 Log Monitoring
```bash
# Django logs
sudo tail -f /var/log/mailbox.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u mailbox -f
```

### 5.2 Update Process
```bash
# On server
cd /var/www/esp32-cam-product
git pull origin main
cd django-webapp
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart mailbox
```

### 5.3 Backup Database
```bash
# PostgreSQL backup
pg_dump mailbox_db > backup_$(date +%Y%m%d).sql

# Restore
psql mailbox_db < backup_20251224.sql
```

## Troubleshooting

### ESP32 Not Connecting
- Check WiFi credentials
- Verify server IP is correct
- Check serial monitor for errors

### Server Not Receiving Requests
- Check firewall: `sudo ufw allow 80/tcp`
- Verify Nginx is running: `sudo systemctl status nginx`
- Check Django logs

### Database Errors
- Verify database credentials in `.env`
- Run migrations: `python manage.py migrate`
- Check PostgreSQL is running: `sudo systemctl status postgresql`

### Static Files Not Loading
- Run: `python manage.py collectstatic`
- Check Nginx static file configuration
- Verify file permissions

## Quick Reference

### Server Commands
```bash
# Restart Django
sudo supervisorctl restart mailbox

# Restart Nginx
sudo systemctl restart nginx

# View logs
sudo tail -f /var/log/mailbox.log

# Update code
cd /var/www/esp32-cam-product && git pull && cd django-webapp && source venv/bin/activate && python manage.py migrate && sudo supervisorctl restart mailbox
```

### ESP32 Commands
```bash
# Upload firmware
cd esp32-firmware && pio run --target upload

# Monitor serial
pio device monitor
```

## Next Steps After Deployment

1. ✅ Test all functionality
2. ✅ Monitor logs for errors
3. ✅ Set up automated backups
4. ✅ Configure monitoring alerts
5. ✅ Document any custom configurations
6. ✅ Train users on the system

## Support

If you encounter issues:
1. Check logs first
2. Verify all configurations
3. Test each component individually
4. Review this guide for missed steps

Good luck with your deployment! 🚀

