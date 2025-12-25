#!/bin/bash
# Setup Nginx for Smart Mailbox - Run on Server

echo "Setting up Nginx..."

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    sudo apt update
    sudo apt install nginx -y
fi

# Create Nginx configuration
echo "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/smartmailbox > /dev/null << 'EOF'
server {
    listen 80;
    server_name 194.164.59.137;

    # Increase body size for image uploads
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /var/www/smartmailbox/django-webapp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/smartmailbox/django-webapp/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF

# Enable site
echo "Enabling site..."
sudo ln -sf /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
echo "Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Restarting Nginx..."
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    echo ""
    echo "✅ Nginx setup complete!"
    echo "✅ Your app is now accessible at: http://194.164.59.137"
    echo "✅ (No port number needed!)"
else
    echo "❌ Nginx configuration error. Please check the config file."
    exit 1
fi

