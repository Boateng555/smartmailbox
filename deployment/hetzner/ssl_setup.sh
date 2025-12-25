#!/bin/bash
# SSL Certificate Setup for Let's Encrypt
# Usage: sudo bash ssl_setup.sh yourdomain.com admin@yourdomain.com

set -e

DOMAIN=${1:-"yourcamera.com"}
EMAIL=${2:-"admin@${DOMAIN}"}

if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root or with sudo"
    exit 1
fi

echo "=========================================="
echo "SSL Certificate Setup"
echo "=========================================="
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Ensure Nginx is running
systemctl start nginx

# Obtain certificate
certbot --nginx \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive \
    --redirect

# Test renewal
certbot renew --dry-run

# Setup auto-renewal cron
(crontab -l 2>/dev/null | grep -v certbot; echo "0 0 1 * * certbot renew --quiet --deploy-hook 'systemctl reload nginx'") | crontab -

echo ""
echo "SSL certificate installed successfully!"
echo "Test SSL: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo ""







