# Mobile Access Setup Guide

## Problem
Server works on computer but not accessible from phone.

## Solutions

### 1. Check Network Connection
- Make sure your phone is on the **same network** as your computer, OR
- Make sure your phone can access the public IP `194.164.59.137`

### 2. Try Different URLs on Phone

Try these URLs in your phone's browser:
- `http://194.164.59.137:8000`
- `http://194.164.59.137:8000/login/`
- `http://194.164.59.137` (if Nginx is set up)

### 3. Setup Nginx (Recommended for Production)

This will make the app accessible on standard port 80 (no need for :8000):

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/smartmailbox
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name 194.164.59.137;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/smartmailbox/django-webapp/staticfiles/;
    }

    location /media/ {
        alias /var/www/smartmailbox/django-webapp/media/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Now access: `http://194.164.59.137` (no port needed!)

### 4. Check Cloud Provider Firewall

If using Hetzner, AWS, etc.:
- Go to your cloud provider's dashboard
- Check firewall/security groups
- Ensure port 80 and 8000 are open for incoming traffic

### 5. Test from Phone

After Nginx setup:
- Open browser on phone
- Go to: `http://194.164.59.137`
- Should see login page

### 6. For HTTPS (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Quick Setup Script

Run this on your server:

```bash
# Install Nginx
sudo apt install nginx -y

# Create config
sudo tee /etc/nginx/sites-available/smartmailbox > /dev/null << 'EOF'
server {
    listen 80;
    server_name 194.164.59.137;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/smartmailbox/django-webapp/staticfiles/;
    }

    location /media/ {
        alias /var/www/smartmailbox/django-webapp/media/;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t
sudo systemctl restart nginx
```

After this, access: `http://194.164.59.137` from your phone!

