#!/bin/bash
# ============================================================================
# Complete Installation - Run This Now on Your Server
# Copy and paste everything from here to the end
# ============================================================================

echo "=========================================="
echo "Installing Smart Camera Server Software"
echo "=========================================="

# Create directory
mkdir -p /var/www/smartcamera
mkdir -p /var/log/smartcamera

# Update system
echo "Updating system..."
apt-get update && apt-get upgrade -y

# Install Python 3.11
echo "Installing Python 3.11..."
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 -m pip install --upgrade pip
echo "✓ Python 3.11 installed"

# Install PostgreSQL
echo "Installing PostgreSQL..."
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
echo "DB_PASSWORD=$DB_PASSWORD" > /root/db_password.txt
chmod 600 /root/db_password.txt
echo "✓ PostgreSQL installed"
echo "✓ Database: smartcamera_db"
echo "✓ User: smartcamera"
echo "✓ Password saved to: /root/db_password.txt"
echo "  Password: $DB_PASSWORD"

# Install Redis
echo "Installing Redis..."
apt-get install -y redis-server
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server
echo "✓ Redis installed"

# Install Nginx
echo "Installing Nginx..."
apt-get install -y nginx
systemctl start nginx
systemctl enable nginx
echo "✓ Nginx installed"

# Install Certbot
echo "Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx
echo "✓ Certbot installed"

# Install Supervisor
echo "Installing Supervisor..."
apt-get install -y supervisor
systemctl start supervisor
systemctl enable supervisor
echo "✓ Supervisor installed"

# Install utilities
echo "Installing utilities..."
apt-get install -y git curl wget htop ufw build-essential libpq-dev libssl-dev libffi-dev
echo "✓ Utilities installed"

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
echo "✓ Firewall configured"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Installed:"
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
echo "Next: Upload your code to /var/www/smartcamera"
echo "=========================================="


