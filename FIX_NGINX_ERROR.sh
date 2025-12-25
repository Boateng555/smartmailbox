#!/bin/bash
# Fix Nginx Configuration Error

echo "Fixing Nginx configuration..."

# Remove problematic configs
sudo rm -f /etc/nginx/sites-enabled/smartcamera
sudo rm -f /etc/nginx/sites-enabled/default

# Create correct config
sudo tee /etc/nginx/sites-available/smartmailbox > /dev/null << 'EOF'
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
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/

# Test and restart
echo "Testing configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Restarting Nginx..."
    sudo systemctl restart nginx
    echo ""
    echo "✅ Nginx fixed and running!"
    echo "✅ Access at: http://194.164.59.137"
else
    echo "❌ Still have errors. Checking nginx.conf..."
    sudo nginx -T | grep smartcamera
    exit 1
fi

