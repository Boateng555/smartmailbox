# Quick Reference - Deployment Commands

## Initial Setup (One-time)

```bash
# 1. Run setup script
sudo bash deployment/setup.sh

# 2. Configure environment
cd /var/www/smartcamera/django-webapp
cp .env.example .env
nano .env

# 3. Set up application
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=iot_platform.settings_production
python manage.py collectstatic --noinput --settings=iot_platform.settings_production

# 4. Configure Nginx
sudo cp deployment/nginx.conf /etc/nginx/sites-available/smartcamera
sudo ln -s /etc/nginx/sites-available/smartcamera /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 5. Set up services
sudo cp deployment/django.service /etc/systemd/system/
sudo cp deployment/daphne.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now django.service daphne.service

# 6. SSL Certificate
sudo certbot --nginx -d yourdomain.com
```

## Regular Deployment

```bash
cd /var/www/smartcamera
bash deployment/deploy.sh
```

## Service Management

```bash
# Start services
sudo systemctl start django.service daphne.service

# Stop services
sudo systemctl stop django.service daphne.service

# Restart services
sudo systemctl restart django.service daphne.service

# Reload Nginx
sudo systemctl reload nginx

# Check status
sudo systemctl status django.service
sudo systemctl status daphne.service
```

## Viewing Logs

```bash
# Django logs
sudo journalctl -u django.service -f

# Daphne logs (WebSocket)
sudo journalctl -u daphne.service -f

# Nginx logs
sudo tail -f /var/log/nginx/smartcamera-error.log
sudo tail -f /var/log/nginx/smartcamera-access.log

# Application logs
tail -f /var/www/smartcamera/django-webapp/logs/django.log
```

## Database Management

```bash
# Connect to database
sudo -u postgres psql -d smartcamera_db

# Backup database
pg_dump -U smartcamera smartcamera_db > backup.sql

# Restore database
psql -U smartcamera smartcamera_db < backup.sql

# Run migrations
cd /var/www/smartcamera/django-webapp
source venv/bin/activate
python manage.py migrate --settings=iot_platform.settings_production
```

## Troubleshooting

```bash
# Test Django configuration
cd /var/www/smartcamera/django-webapp
source venv/bin/activate
python manage.py check --settings=iot_platform.settings_production

# Test Nginx configuration
sudo nginx -t

# Check Redis
redis-cli ping

# Check PostgreSQL
sudo systemctl status postgresql
```







