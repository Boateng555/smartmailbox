#!/bin/bash
# Let's Encrypt SSL Certificate Setup Script
# Usage: ./setup-letsencrypt.sh yourcamera.com admin@yourcamera.com

set -e

DOMAIN=${1:-"yourcamera.com"}
EMAIL=${2:-"admin@${DOMAIN}"}

echo "=========================================="
echo "Let's Encrypt SSL Certificate Setup"
echo "=========================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Check if domain is provided
if [ -z "$DOMAIN" ] || [ "$DOMAIN" == "yourcamera.com" ]; then
    echo "ERROR: Please provide your domain name"
    echo "Usage: ./setup-letsencrypt.sh yourcamera.com admin@yourcamera.com"
    exit 1
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root or with sudo"
    exit 1
fi

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create directory for certbot challenges
mkdir -p nginx/certbot
chmod 755 nginx/certbot

# Ensure nginx is running (for initial certificate)
echo "Starting nginx container..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
echo "Waiting for nginx to be ready..."
sleep 5

# Obtain certificate using webroot method (works with nginx running)
echo "Obtaining SSL certificate from Let's Encrypt..."
certbot certonly --webroot \
    --webroot-path=$(pwd)/nginx/certbot \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

# Verify certificates were created
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "ERROR: Certificate files not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "SSL Certificate installed successfully!"
echo "=========================================="
echo ""
echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
echo ""
echo "Next steps:"
echo "1. Update nginx/conf.d/yourcamera.com.conf with your domain"
echo "2. Restart nginx: docker-compose -f docker-compose.prod.yml restart nginx"
echo "3. Test SSL: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""
echo "Auto-renewal setup:"
echo "Add to crontab (crontab -e):"
echo "0 0 1 * * certbot renew --quiet --deploy-hook 'docker-compose -f docker-compose.prod.yml restart nginx'"
echo ""







