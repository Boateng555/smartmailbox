#!/bin/bash
# Generate self-signed certificate for initial setup

set -e

DOMAIN=${1:-"localhost"}

echo "Generating self-signed certificate for $DOMAIN..."

mkdir -p nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

chmod 600 nginx/ssl/privkey.pem
chmod 644 nginx/ssl/fullchain.pem

echo "Self-signed certificate generated in nginx/ssl/"
echo "Replace with Let's Encrypt certificate using setup-ssl.sh"







