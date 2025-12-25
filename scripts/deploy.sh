#!/bin/bash
# Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "=========================================="
echo "Smart Mailbox Production Deployment"
echo "=========================================="
echo ""

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "ERROR: .env.production not found!"
    echo "Copy .env.production.example to .env.production and configure it"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose not found!"
    exit 1
fi

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code..."
    git pull
fi

# Build and start services
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Restart web service to apply changes
echo "Restarting web service..."
docker-compose -f docker-compose.prod.yml restart web

# Check service status
echo ""
echo "Service Status:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "Deployment completed!"
echo "=========================================="
echo ""
echo "Check logs with: docker-compose -f docker-compose.prod.yml logs -f"
echo ""







