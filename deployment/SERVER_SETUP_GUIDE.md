# Complete Server Setup Guide
## Ubuntu Server at 194.164.59.137

This guide will help you set up everything needed on your server.

## Step 1: Connect to Your Server

```bash
ssh root@194.164.59.137
```

## Step 2: Update System

```bash
apt-get update
apt-get upgrade -y
```

## Step 3: Install Required Software

Run the setup script that installs everything:

```bash
# First, you need to get the code on the server
# Option 1: If you have git repository
git clone YOUR_REPO_URL /var/www/smartcamera

# Option 2: If you need to upload files manually
# Create directory first
mkdir -p /var/www/smartcamera
# Then upload your files via SCP or SFTP

# Go to deployment directory
cd /var/www/smartcamera/deployment

# Make setup script executable
chmod +x setup.sh

# Run setup (this installs everything)
sudo bash setup.sh
```

**What gets installed:**
- ✅ Python 3.11
- ✅ PostgreSQL (database)
- ✅ Redis (for WebSockets)
- ✅ Nginx (web server)
- ✅ Certbot (for SSL certificates)
- ✅ Supervisor (process manager)
- ✅ Git and other utilities

## Step 4: Set Up Django Application

```bash
cd /var/www/smartcamera/django-webapp

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install all Python packages
pip install -r requirements.txt
```

## Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit the .env file
nano .env
```

**Required values in .env file:**

```bash
# Generate SECRET_KEY (run this command):
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Then add to .env:
SECRET_KEY=your_generated_secret_key_here
DEBUG=False
ALLOWED_HOSTS=194.164.59.137,yourdomain.com
API_DOMAIN=194.164.59.137

# Database (use password from setup.sh or change it)
DATABASE_URL=postgresql://smartcamera:CHANGE_THIS_PASSWORD@localhost:5432/smartcamera_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Push notifications (optional for now)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_ADMIN_EMAIL=your@email.com
```

## Step 6: Set Up Database

```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Run database migrations
python manage.py migrate --settings=iot_platform.settings_production

# Create admin user
python manage.py createsuperuser --settings=iot_platform.settings_production
```

## Step 7: Collect Static Files

```bash
# Still in virtual environment
python manage.py collectstatic --noinput --settings=iot_platform.settings_production
```

## Step 8: Configure Nginx

**For IP address only (no SSL):**
```bash
# Use the IP-only config
cp /var/www/smartcamera/deployment/nginx-ip-only.conf /etc/nginx/sites-available/smartcamera
```

**For domain with SSL:**
```bash
# Edit nginx config (replace YOUR_DOMAIN.com with your domain)
nano /var/www/smartcamera/deployment/nginx.conf

# Copy to Nginx
cp /var/www/smartcamera/deployment/nginx.conf /etc/nginx/sites-available/smartcamera
```

# Enable the site
ln -s /etc/nginx/sites-available/smartcamera /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# If test passes, reload Nginx
systemctl reload nginx
```

## Step 9: Set Up Systemd Services

```bash
# Copy service files
cp /var/www/smartcamera/deployment/django.service /etc/systemd/system/
cp /var/www/smartcamera/deployment/daphne.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable services (start on boot)
systemctl enable django.service
systemctl enable daphne.service

# Start services
systemctl start django.service
systemctl start daphne.service
```

## Step 10: Check Everything is Working

```bash
# Check service status
systemctl status django.service
systemctl status daphne.service
systemctl status nginx.service

# Check logs if there are errors
journalctl -u django.service -n 50
journalctl -u daphne.service -n 50
```

## Step 11: Configure Firewall (if not done)

```bash
# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # For Django (if testing directly)

# Check firewall status
ufw status
```

## Step 12: Test Your Server

Open in browser:
- `http://194.164.59.137` - Should show your Django app
- `http://194.164.59.137:8000` - Direct Django (if firewall allows)

## Quick Commands Reference

```bash
# Restart services
systemctl restart django.service
systemctl restart daphne.service
systemctl reload nginx

# View logs
journalctl -u django.service -f
journalctl -u daphne.service -f
tail -f /var/log/nginx/error.log

# Check if services are running
systemctl status django.service
systemctl status daphne.service
```

## Troubleshooting

### If Django service won't start:
```bash
# Check logs
journalctl -u django.service -n 50

# Test manually
cd /var/www/smartcamera/django-webapp
source venv/bin/activate
python manage.py check --settings=iot_platform.settings_production
```

### If database connection fails:
```bash
# Test PostgreSQL
sudo -u postgres psql -c "SELECT version();"

# Check database exists
sudo -u postgres psql -l | grep smartcamera
```

### If Nginx gives errors:
```bash
# Test configuration
nginx -t

# Check error logs
tail -f /var/log/nginx/error.log
```

## Next Steps After Setup

1. **Set up SSL certificate** (if you have a domain):
   ```bash
   certbot --nginx -d yourdomain.com
   ```

2. **Configure domain** (if you have one):
   - Point your domain to 194.164.59.137
   - Update ALLOWED_HOSTS in .env
   - Update API_DOMAIN in ESP32 firmware

3. **Test ESP32 connection**:
   - Make sure ESP32 firmware has: `API_DOMAIN = "194.164.59.137"`
   - Turn on ESP32 device
   - Check if it connects and sends photos

## Important Notes

- **PostgreSQL Password**: Change `CHANGE_THIS_PASSWORD` in setup.sh or update .env file
- **SECRET_KEY**: Must be unique and secret - generate a new one
- **ALLOWED_HOSTS**: Must include your IP (194.164.59.137) or domain
- **Port 8000**: Django runs on port 8000, Nginx proxies to it
- **Firewall**: Make sure ports 80 and 443 are open

## File Locations

- Application: `/var/www/smartcamera/django-webapp`
- Logs: `/var/log/smartcamera`
- Nginx config: `/etc/nginx/sites-available/smartcamera`
- Service files: `/etc/systemd/system/django.service` and `/etc/systemd/system/daphne.service`

