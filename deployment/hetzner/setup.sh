#!/bin/bash
# Production Deployment Setup Script for Hetzner CPX11
# Ubuntu 22.04 LTS
# Usage: sudo bash setup.sh

set -e

echo "=========================================="
echo "Hetzner CPX11 Production Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root or with sudo"
    exit 1
fi

# Configuration
DOMAIN=${1:-"yourcamera.com"}
DB_NAME=${DB_NAME:-"smartmailbox"}
DB_USER=${DB_USER:-"smartmailbox_user"}
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
DJANGO_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 50)

echo "Domain: $DOMAIN"
echo "Database: $DB_NAME"
echo "Database User: $DB_USER"
echo ""

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install essential packages
echo "Installing essential packages..."
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx \
    supervisor \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    ufw \
    awscli \
    htop \
    fail2ban \
    logrotate

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw status

# Create application user
echo "Creating application user..."
if ! id -u smartmailbox >/dev/null 2>&1; then
    useradd -m -s /bin/bash smartmailbox
    usermod -aG sudo smartmailbox
fi

# Setup application directory
APP_DIR="/opt/smartmailbox"
echo "Setting up application directory: $APP_DIR"
mkdir -p $APP_DIR
chown smartmailbox:smartmailbox $APP_DIR

# Configure PostgreSQL
echo "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;" || true

# Configure Redis
echo "Configuring Redis..."
sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
sed -i "s/bind 127.0.0.1/bind 127.0.0.1/" /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
sudo -u smartmailbox python3.11 -m venv $APP_DIR/venv
sudo -u smartmailbox $APP_DIR/venv/bin/pip install --upgrade pip setuptools wheel

# Create directories
echo "Creating application directories..."
mkdir -p $APP_DIR/{logs,static,media,backups}
chown -R smartmailbox:smartmailbox $APP_DIR

# Setup Nginx
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/smartmailbox <<EOF
# Upstream for Django
upstream django {
    server 127.0.0.1:8001;
    keepalive 32;
}

# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/smartmailbox-access.log;
    error_log /var/log/nginx/smartmailbox-error.log;

    # Client settings
    client_max_body_size 20M;
    client_body_buffer_size 128k;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;

    # Static files
    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400s;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
    }

    # Dashboard
    location /dashboard/ {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Root and other locations
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/smartmailbox /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Setup Supervisor
echo "Configuring Supervisor..."
cat > /etc/supervisor/conf.d/smartmailbox.conf <<EOF
[program:smartmailbox]
command=$APP_DIR/venv/bin/daphne -b 127.0.0.1 -p 8001 iot_platform.asgi:application
directory=$APP_DIR/django-webapp
user=smartmailbox
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/daphne.log
environment=DJANGO_SETTINGS_MODULE="iot_platform.settings_production"
EOF

# Create environment file template
echo "Creating environment file template..."
cat > $APP_DIR/.env.production <<EOF
# Django Settings
DEBUG=False
SECRET_KEY=$DJANGO_SECRET_KEY
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DJANGO_SETTINGS_MODULE=iot_platform.settings_production

# Domain
DOMAIN=$DOMAIN
API_DOMAIN=$DOMAIN

# Database
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASSWORD

# Email (configure with your provider)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=noreply@$DOMAIN

# AWS S3 Backup (configure with your credentials)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET=smartmailbox-backups
EOF

chown smartmailbox:smartmailbox $APP_DIR/.env.production
chmod 600 $APP_DIR/.env.production

# Setup log rotation
echo "Configuring log rotation..."
cat > /etc/logrotate.d/smartmailbox <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 smartmailbox smartmailbox
    sharedscripts
    postrotate
        supervisorctl restart smartmailbox > /dev/null 2>&1 || true
    endscript
}
EOF

# Setup fail2ban
echo "Configuring fail2ban..."
cat > /etc/fail2ban/jail.d/nginx.conf <<EOF
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

systemctl restart fail2ban
systemctl enable fail2ban

# Create backup script
echo "Creating backup script..."
cat > $APP_DIR/backup.sh <<'BACKUP_SCRIPT'
#!/bin/bash
# Daily backup script
set -e

APP_DIR="/opt/smartmailbox"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$APP_DIR/backups"
S3_BUCKET=${S3_BUCKET:-"smartmailbox-backups"}

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump smartmailbox | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup media files
tar czf $BACKUP_DIR/media_$TIMESTAMP.tar.gz -C $APP_DIR media/

# Upload to S3 if configured
if [ ! -z "$AWS_ACCESS_KEY_ID" ] && [ ! -z "$AWS_SECRET_ACCESS_KEY" ]; then
    aws s3 sync $BACKUP_DIR s3://$S3_BUCKET/backups/ --exclude "*" --include "*.gz" --include "*.tar.gz"
    # Clean up local backups older than 7 days
    find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
    find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
fi

echo "Backup completed: $TIMESTAMP"
BACKUP_SCRIPT

chmod +x $APP_DIR/backup.sh
chown smartmailbox:smartmailbox $APP_DIR/backup.sh

# Setup daily backup cron
echo "Setting up daily backup cron..."
(crontab -u smartmailbox -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh >> $APP_DIR/logs/backup.log 2>&1") | crontab -u smartmailbox -

# Create deployment script
echo "Creating deployment script..."
cat > $APP_DIR/deploy.sh <<'DEPLOY_SCRIPT'
#!/bin/bash
# Deployment script
set -e

APP_DIR="/opt/smartmailbox"
cd $APP_DIR/django-webapp

# Activate virtual environment
source $APP_DIR/venv/bin/activate

# Pull latest code (if using git)
# git pull

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Restart application
supervisorctl restart smartmailbox

echo "Deployment completed"
DEPLOY_SCRIPT

chmod +x $APP_DIR/deploy.sh
chown smartmailbox:smartmailbox $APP_DIR/deploy.sh

echo ""
echo "=========================================="
echo "Setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Point $DOMAIN DNS A record to this server IP"
echo "2. Wait for DNS propagation (check with: dig $DOMAIN)"
echo "3. Run SSL setup: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "4. Clone your repository to $APP_DIR/django-webapp"
echo "5. Run: sudo -u smartmailbox $APP_DIR/deploy.sh"
echo ""
echo "Configuration saved to: $APP_DIR/.env.production"
echo "Database password: $DB_PASSWORD"
echo "Redis password: $REDIS_PASSWORD"
echo ""
echo "IMPORTANT: Save these passwords securely!"
echo ""







