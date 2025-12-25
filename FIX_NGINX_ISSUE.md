# Fix Nginx Configuration Error

## Problem
Nginx is looking for `/etc/nginx/sites-enabled/smartcamera` but it doesn't exist.

## Solution

### Step 1: Check Existing Nginx Configs
```bash
ls -la /etc/nginx/sites-enabled/
```

### Step 2: Remove Problematic Config (if exists)
```bash
sudo rm -f /etc/nginx/sites-enabled/smartcamera
```

### Step 3: Manual Nginx Setup

```bash
# Create config file
sudo nano /etc/nginx/sites-available/smartmailbox
```

Paste this:
```nginx
server {
    listen 80;
    server_name 194.164.59.137;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /var/www/smartmailbox/django-webapp/staticfiles/;
    }

    location /media/ {
        alias /var/www/smartmailbox/django-webapp/media/;
    }
}
```

Then:
```bash
# Enable site
sudo ln -sf /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/smartcamera

# Test and restart
sudo nginx -t
sudo systemctl restart nginx
```

## Port 8000 Already in Use

The Django server is already running. That's good! You don't need to restart it.

Check what's running:
```bash
ps aux | grep manage.py
```

If you need to stop it:
```bash
# Find the process
ps aux | grep manage.py

# Kill it (replace PID with actual process ID)
kill PID

# Or kill all Python manage.py processes
pkill -f "manage.py runserver"
```

## After Fix

✅ Nginx should work
✅ Access: `http://194.164.59.137` (no port)
✅ Django server already running on port 8000

