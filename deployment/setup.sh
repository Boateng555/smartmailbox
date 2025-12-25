#!/bin/bash
# ============================================================================
# Hetzner Ubuntu Server Setup Script
# ============================================================================
# This script installs all required dependencies for Django deployment
# Run as: sudo bash setup.sh
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "Hetzner Ubuntu Server Setup"
echo "=========================================="

# Update system packages
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# ============================================================================
# Install Python 3.11 and pip
# ============================================================================
echo "Installing Python 3.11..."
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install pip for Python 3.11
python3.11 -m pip install --upgrade pip

# ============================================================================
# Install PostgreSQL
# ============================================================================
echo "Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Create database and user (adjust as needed)
echo "Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
-- Create database user
CREATE USER smartcamera WITH PASSWORD 'CHANGE_THIS_PASSWORD';
-- Create database
CREATE DATABASE smartcamera_db OWNER smartcamera;
-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE smartcamera_db TO smartcamera;
\q
EOF

echo "PostgreSQL installed. Remember to update the password in .env file!"

# ============================================================================
# Install Redis
# ============================================================================
echo "Installing Redis..."
apt-get install -y redis-server

# Configure Redis
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Start and enable Redis
systemctl restart redis-server
systemctl enable redis-server

# ============================================================================
# Install Nginx
# ============================================================================
echo "Installing Nginx..."
apt-get install -y nginx

# Start and enable Nginx
systemctl start nginx
systemctl enable nginx

# ============================================================================
# Install Certbot for SSL
# ============================================================================
echo "Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

# ============================================================================
# Install Supervisor for process management
# ============================================================================
echo "Installing Supervisor..."
apt-get install -y supervisor

# Start and enable Supervisor
systemctl start supervisor
systemctl enable supervisor

# ============================================================================
# Install Git (if not already installed)
# ============================================================================
echo "Installing Git..."
apt-get install -y git

# ============================================================================
# Install additional utilities
# ============================================================================
echo "Installing additional utilities..."
apt-get install -y \
    curl \
    wget \
    htop \
    ufw \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev

# ============================================================================
# Configure Firewall
# ============================================================================
echo "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw status

# ============================================================================
# Create application directory
# ============================================================================
echo "Creating application directory..."
APP_DIR="/var/www/smartcamera"
mkdir -p $APP_DIR
chown -R $SUDO_USER:$SUDO_USER $APP_DIR

# ============================================================================
# Create logs directory
# ============================================================================
echo "Creating logs directory..."
LOGS_DIR="/var/log/smartcamera"
mkdir -p $LOGS_DIR
chown -R $SUDO_USER:$SUDO_USER $LOGS_DIR

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Installed components:"
echo "  ✓ Python 3.11"
echo "  ✓ PostgreSQL (database: smartcamera_db, user: smartcamera)"
echo "  ✓ Redis"
echo "  ✓ Nginx"
echo "  ✓ Certbot"
echo "  ✓ Supervisor"
echo ""
echo "Next steps:"
echo "  1. Clone your repository to $APP_DIR"
echo "  2. Create .env file from .env.example"
echo "  3. Set up virtual environment: python3.11 -m venv venv"
echo "  4. Install dependencies: pip install -r requirements.txt"
echo "  5. Run migrations: python manage.py migrate"
echo "  6. Collect static files: python manage.py collectstatic"
echo "  7. Copy nginx.conf to /etc/nginx/sites-available/smartcamera"
echo "  8. Copy django.service to /etc/systemd/system/"
echo "  9. Enable and start services"
echo "  10. Configure SSL with: certbot --nginx -d yourdomain.com"
echo ""
echo "IMPORTANT: Update PostgreSQL password in .env file!"
echo "=========================================="







