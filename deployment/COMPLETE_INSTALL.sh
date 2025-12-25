#!/bin/bash
# ============================================================================
# Complete Installation - Handles Already Installed Packages
# ============================================================================

echo "=========================================="
echo "Smart Camera Server Installation"
echo "=========================================="

# Create directories
mkdir -p /var/www/smartcamera
mkdir -p /var/log/smartcamera

# Update system
echo "Updating system..."
apt-get update -qq
apt-get upgrade -y -qq

# Install Python 3.11 (if not already installed)
echo "Checking Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    apt-get install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
    python3.11 -m pip install --upgrade pip --quiet
    echo "✓ Python 3.11 installed"
else
    echo "✓ Python 3.11 already installed"
fi

# Install PostgreSQL (if not already installed)
echo "Checking PostgreSQL..."
if ! systemctl is-active --quiet postgresql; then
    apt-get install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql
    echo "✓ PostgreSQL installed"
else
    echo "✓ PostgreSQL already installed and running"
fi

# Create database (check if exists first)
echo "Setting up database..."
if [ ! -f /root/db_password.txt ]; then
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    echo "DB_PASSWORD=$DB_PASSWORD" > /root/db_password.txt
    chmod 600 /root/db_password.txt
else
    DB_PASSWORD=$(grep DB_PASSWORD /root/db_password.txt | cut -d'=' -f2)
    echo "Using existing database password"
fi

# Create user and database (only if they don't exist)
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='smartcamera'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER smartcamera WITH PASSWORD '$DB_PASSWORD';"

sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='smartcamera_db'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE DATABASE smartcamera_db OWNER smartcamera;"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smartcamera_db TO smartcamera;" 2>/dev/null || true

echo "✓ Database configured"
echo "  Database: smartcamera_db"
echo "  User: smartcamera"
echo "  Password: $DB_PASSWORD"

# Install Redis
echo "Installing Redis..."
if ! systemctl is-active --quiet redis-server; then
    apt-get install -y redis-server
    sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
    sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
    sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    systemctl restart redis-server
    systemctl enable redis-server
    echo "✓ Redis installed"
else
    echo "✓ Redis already installed"
fi

# Install Nginx
echo "Installing Nginx..."
if ! systemctl is-active --quiet nginx; then
    apt-get install -y nginx
    systemctl start nginx
    systemctl enable nginx
    echo "✓ Nginx installed"
else
    echo "✓ Nginx already installed"
fi

# Install Certbot
echo "Installing Certbot..."
if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot python3-certbot-nginx
    echo "✓ Certbot installed"
else
    echo "✓ Certbot already installed"
fi

# Install Supervisor
echo "Installing Supervisor..."
if ! systemctl is-active --quiet supervisor; then
    apt-get install -y supervisor
    systemctl start supervisor
    systemctl enable supervisor
    echo "✓ Supervisor installed"
else
    echo "✓ Supervisor already installed"
fi

# Install utilities
echo "Installing utilities..."
apt-get install -y git curl wget htop ufw build-essential libpq-dev libssl-dev libffi-dev 2>/dev/null
echo "✓ Utilities installed"

# Configure firewall
echo "Configuring firewall..."
if ! ufw status | grep -q "Status: active"; then
    ufw --force enable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    echo "✓ Firewall configured"
else
    echo "✓ Firewall already configured"
    ufw allow 80/tcp 2>/dev/null || true
    ufw allow 443/tcp 2>/dev/null || true
    ufw allow 8000/tcp 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Installed/Verified:"
echo "  ✓ Python 3.11"
echo "  ✓ PostgreSQL (database: smartcamera_db)"
echo "  ✓ Redis"
echo "  ✓ Nginx"
echo "  ✓ Certbot"
echo "  ✓ Supervisor"
echo "  ✓ All utilities"
echo ""
echo "Database Password: $DB_PASSWORD"
echo "Saved to: /root/db_password.txt"
echo ""
echo "Next Steps:"
echo "  1. Upload your code to /var/www/smartcamera"
echo "  2. cd /var/www/smartcamera/django-webapp"
echo "  3. python3.11 -m venv venv"
echo "  4. source venv/bin/activate"
echo "  5. pip install -r requirements.txt"
echo "=========================================="


