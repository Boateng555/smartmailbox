# Hetzner Cloud Deployment Guide

This directory contains deployment scripts and configuration files for deploying the Smart Camera IoT Platform to a Hetzner Ubuntu server.

## Files Overview

- **setup.sh** - Initial server setup script (run once)
- **django.service** - Systemd service file for Django/Gunicorn
- **daphne.service** - Systemd service file for WebSocket support
- **nginx.conf** - Nginx reverse proxy configuration
- **deploy.sh** - Deployment script for updating the application

## Quick Start

### 1. Initial Server Setup

SSH into your Hetzner server and run:

```bash
# Clone the repository
git clone https://github.com/yourusername/esp32-cam-product.git /var/www/smartcamera

# Run setup script
cd /var/www/smartcamera/deployment
sudo bash setup.sh
```

This will install:
- Python 3.11
- PostgreSQL
- Redis
- Nginx
- Certbot (for SSL)
- Supervisor
- All required dependencies

### 2. Configure Environment

```bash
cd /var/www/smartcamera/django-webapp
cp .env.example .env
nano .env  # Edit with your values
```

**Required variables:**
- `SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS` - Your domain(s), comma-separated
- `API_DOMAIN` - Domain for ESP32 devices
- `DATABASE_URL` - PostgreSQL connection string

### 3. Set Up Application

```bash
cd /var/www/smartcamera/django-webapp

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
python manage.py migrate --settings=iot_platform.settings_production

# Create superuser
python manage.py createsuperuser --settings=iot_platform.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=iot_platform.settings_production
```

### 4. Configure Nginx

```bash
# Edit nginx.conf and replace YOUR_DOMAIN.com with your domain
sudo nano deployment/nginx.conf

# Copy to Nginx sites
sudo cp deployment/nginx.conf /etc/nginx/sites-available/smartcamera
sudo ln -s /etc/nginx/sites-available/smartcamera /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 5. Set Up Systemd Services

```bash
# Copy service files
sudo cp deployment/django.service /etc/systemd/system/
sudo cp deployment/daphne.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable django.service
sudo systemctl enable daphne.service
sudo systemctl start django.service
sudo systemctl start daphne.service
```

### 6. Configure SSL with Let's Encrypt

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Certbot will automatically update nginx.conf
# Test auto-renewal
sudo certbot renew --dry-run
```

### 7. Verify Deployment

```bash
# Check service status
sudo systemctl status django.service
sudo systemctl status daphne.service
sudo systemctl status nginx.service

# Check logs
sudo journalctl -u django.service -f
sudo journalctl -u daphne.service -f
sudo tail -f /var/log/nginx/smartcamera-error.log
```

## Deployment Workflow

After initial setup, use the deployment script to update:

```bash
cd /var/www/smartcamera
bash deployment/deploy.sh
```

This script will:
1. Pull latest code from git
2. Update Python dependencies
3. Run database migrations
4. Collect static files
5. Restart all services

## Service Management

```bash
# Restart services
sudo systemctl restart django.service
sudo systemctl restart daphne.service
sudo systemctl reload nginx

# View logs
sudo journalctl -u django.service -f
sudo journalctl -u daphne.service -f

# Check status
sudo systemctl status django.service
sudo systemctl status daphne.service
```

## Troubleshooting

### Django service won't start
```bash
# Check logs
sudo journalctl -u django.service -n 50

# Check environment file
cat /var/www/smartcamera/django-webapp/.env

# Test manually
cd /var/www/smartcamera/django-webapp
source venv/bin/activate
python manage.py check --settings=iot_platform.settings_production
```

### Nginx errors
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/smartcamera-error.log
```

### Database connection issues
```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "SELECT version();"

# Check database exists
sudo -u postgres psql -l | grep smartcamera
```

## Security Checklist

- [ ] Change PostgreSQL password in .env
- [ ] Set strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS correctly
- [ ] Enable SSL with Let's Encrypt
- [ ] Configure firewall (UFW)
- [ ] Set up log rotation
- [ ] Configure automatic backups
- [ ] Set up monitoring

## File Permissions

Ensure correct permissions:

```bash
# Application directory
sudo chown -R www-data:www-data /var/www/smartcamera/django-webapp
sudo chmod -R 755 /var/www/smartcamera

# Logs directory
sudo chown -R www-data:www-data /var/log/smartcamera
sudo chmod -R 755 /var/log/smartcamera

# Media directory (writable)
sudo chown -R www-data:www-data /var/www/smartcamera/django-webapp/media
sudo chmod -R 775 /var/www/smartcamera/django-webapp/media
```

## Backup

Set up regular backups:

```bash
# Database backup
pg_dump -U smartcamera smartcamera_db > backup_$(date +%Y%m%d).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz /var/www/smartcamera/django-webapp/media/
```







