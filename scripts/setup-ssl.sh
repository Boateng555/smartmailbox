#!/bin/bash
# SSL Certificate Setup Script with Let's Encrypt

set -e

DOMAIN=${1:-"yourdomain.com"}
EMAIL=${2:-"admin@${DOMAIN}"}

echo "Setting up SSL certificate for domain: $DOMAIN"
echo "Email: $EMAIL"

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create directory for certbot challenges
mkdir -p /var/www/certbot

# Stop nginx temporarily
docker-compose stop nginx

# Obtain certificate
certbot certonly --standalone \
    --preferred-challenges http \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive

# Copy certificates to nginx ssl directory
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/fullchain.pem
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/privkey.pem

# Set proper permissions
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem

# Start nginx
docker-compose start nginx

echo "SSL certificate installed successfully!"
echo "Certificates are located in: nginx/ssl/"
echo ""
echo "To renew certificates, run: certbot renew"
echo "Add to crontab for auto-renewal: 0 0 1 * * certbot renew --quiet"







