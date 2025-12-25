# Complete Nginx Setup Guide

## Files Created

1. `nginx/nginx.conf` - Main Nginx configuration
2. `nginx/smartmailbox.conf` - Smart Mailbox server configuration

## Setup Instructions

### On Your Server:

```bash
# 1. Backup existing nginx.conf
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup

# 2. Copy new nginx.conf (optional - only if you want to replace main config)
# Or just use the sites-available method below

# 3. Create smartmailbox config
sudo nano /etc/nginx/sites-available/smartmailbox
```

Copy the content from `nginx/smartmailbox.conf` and paste it.

### Or Use the Config File Directly:

```bash
cd /var/www/smartmailbox
git pull origin main

# Copy config to Nginx
sudo cp nginx/smartmailbox.conf /etc/nginx/sites-available/smartmailbox

# Enable site
sudo ln -sf /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/smartcamera

# Test configuration
sudo nginx -t

# If test passes, restart
sudo systemctl restart nginx
```

## What This Configuration Does

✅ **Listens on port 80** - Standard HTTP port
✅ **Proxies to Django** - Forwards requests to port 8000
✅ **Serves static files** - Directly from Nginx (faster)
✅ **WebSocket support** - For real-time updates
✅ **Large file uploads** - 10MB max body size
✅ **Health check** - `/health/` endpoint

## After Setup

Access your app at: `http://194.164.59.137` (no port needed!)

## Verify It Works

```bash
# Check Nginx status
sudo systemctl status nginx

# Check if listening on port 80
sudo netstat -tlnp | grep :80

# Test from server
curl http://localhost
```

## Troubleshooting

If you get errors:
```bash
# Check Nginx error log
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t

# Check what's in sites-enabled
ls -la /etc/nginx/sites-enabled/
```

