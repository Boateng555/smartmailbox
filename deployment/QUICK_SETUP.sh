#!/bin/bash
# ============================================================================
# Quick Setup Script for Ubuntu Server
# Run this on your server: sudo bash QUICK_SETUP.sh
# ============================================================================

set -e

echo "=========================================="
echo "Smart Camera Server Quick Setup"
echo "Server IP: 194.164.59.137"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Step 1: Update system
echo ""
echo "Step 1: Updating system packages..."
apt-get update
apt-get upgrade -y

# Step 2: Install Python 3.11
echo ""
echo "Step 2: Installing Python 3.11..."
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 -m pip install --upgrade pip

# Step 3: Install PostgreSQL
echo ""
echo "Step 3: Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql

# Create database
echo "Creating database..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
sudo -u postgres psql << EOF
CREATE USER smartcamera WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE smartcamera_db OWNER smartcamera;
GRANT ALL PRIVILEGES ON DATABASE smartcamera_db TO smartcamera;
\q
EOF
echo "Database created! Password saved to /root/db_password.txt"
echo "DB_PASSWORD=$DB_PASSWORD" > /root/db_password.txt
chmod 600 /root/db_password.txt

# Step 4: Install Redis
echo ""
echo "Step 4: Installing Redis..."
apt-get install -y redis-server
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# Step 5: Install Nginx
echo ""
echo "Step 5: Installing Nginx..."
apt-get install -y nginx
systemctl start nginx
systemctl enable nginx

# Step 6: Install Certbot
echo ""
echo "Step 6: Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

# Step 7: Install Supervisor
echo ""
echo "Step 7: Installing Supervisor..."
apt-get install -y supervisor
systemctl start supervisor
systemctl enable supervisor

# Step 8: Install utilities
echo ""
echo "Step 8: Installing utilities..."
apt-get install -y \
    git \
    curl \
    wget \
    htop \
    ufw \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev

# Step 9: Configure firewall
echo ""
echo "Step 9: Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw status

# Step 10: Create directories
echo ""
echo "Step 10: Creating directories..."
mkdir -p /var/www/smartcamera
mkdir -p /var/log/smartcamera
chown -R $SUDO_USER:$SUDO_USER /var/www/smartcamera
chown -R $SUDO_USER:$SUDO_USER /var/log/smartcamera

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Installed:"
echo "  ✓ Python 3.11"
echo "  ✓ PostgreSQL (database: smartcamera_db)"
echo "  ✓ Redis"
echo "  ✓ Nginx"
echo "  ✓ Certbot"
echo "  ✓ Supervisor"
echo ""
echo "Database password saved to: /root/db_password.txt"
echo ""
echo "Next steps:"
echo "  1. Upload your code to /var/www/smartcamera"
echo "  2. Go to: cd /var/www/smartcamera/django-webapp"
echo "  3. Create .env file: cp .env.example .env"
echo "  4. Edit .env and add DATABASE_URL with password from /root/db_password.txt"
echo "  5. Run: python3.11 -m venv venv"
echo "  6. Run: source venv/bin/activate && pip install -r requirements.txt"
echo "  7. Run: python manage.py migrate --settings=iot_platform.settings_production"
echo "  8. Run: python manage.py collectstatic --noinput --settings=iot_platform.settings_production"
echo "  9. Copy nginx.conf and service files"
echo "  10. Start services"
echo ""
echo "See SERVER_SETUP_GUIDE.md for detailed instructions"
echo "=========================================="


