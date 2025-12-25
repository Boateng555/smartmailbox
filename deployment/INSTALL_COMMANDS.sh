#!/bin/bash
# ============================================================================
# Installation Commands for Ubuntu Server
# Run these commands one by one on your server: 194.164.59.137
# ============================================================================

echo "=========================================="
echo "Installing Smart Camera Server Software"
echo "=========================================="

# ============================================================================
# Step 1: Update System
# ============================================================================
echo ""
echo "Step 1: Updating system packages..."
apt-get update
apt-get upgrade -y

# ============================================================================
# Step 2: Install Python 3.11
# ============================================================================
echo ""
echo "Step 2: Installing Python 3.11..."
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 -m pip install --upgrade pip

echo "✓ Python 3.11 installed"
python3.11 --version

# ============================================================================
# Step 3: Install PostgreSQL (Database)
# ============================================================================
echo ""
echo "Step 3: Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Create database and user
echo "Creating database..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
sudo -u postgres psql << EOF
CREATE USER smartcamera WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE smartcamera_db OWNER smartcamera;
GRANT ALL PRIVILEGES ON DATABASE smartcamera_db TO smartcamera;
\q
EOF

# Save password
echo "DB_PASSWORD=$DB_PASSWORD" > /root/db_password.txt
chmod 600 /root/db_password.txt

echo "✓ PostgreSQL installed"
echo "✓ Database created: smartcamera_db"
echo "✓ User created: smartcamera"
echo "✓ Password saved to: /root/db_password.txt"
echo "Password: $DB_PASSWORD"

# ============================================================================
# Step 4: Install Redis (for WebSockets)
# ============================================================================
echo ""
echo "Step 4: Installing Redis..."
apt-get install -y redis-server

# Configure Redis
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Start and enable Redis
systemctl restart redis-server
systemctl enable redis-server

echo "✓ Redis installed and running"
systemctl status redis-server --no-pager | head -3

# ============================================================================
# Step 5: Install Nginx (Web Server)
# ============================================================================
echo ""
echo "Step 5: Installing Nginx..."
apt-get install -y nginx

# Start and enable Nginx
systemctl start nginx
systemctl enable nginx

echo "✓ Nginx installed and running"
systemctl status nginx --no-pager | head -3

# ============================================================================
# Step 6: Install Certbot (for SSL Certificates)
# ============================================================================
echo ""
echo "Step 6: Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

echo "✓ Certbot installed"

# ============================================================================
# Step 7: Install Supervisor (Process Manager)
# ============================================================================
echo ""
echo "Step 7: Installing Supervisor..."
apt-get install -y supervisor

# Start and enable Supervisor
systemctl start supervisor
systemctl enable supervisor

echo "✓ Supervisor installed and running"
systemctl status supervisor --no-pager | head -3

# ============================================================================
# Step 8: Install Utilities
# ============================================================================
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

echo "✓ Utilities installed"

# ============================================================================
# Step 9: Configure Firewall
# ============================================================================
echo ""
echo "Step 9: Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp

echo "✓ Firewall configured"
ufw status

# ============================================================================
# Step 10: Create Directories
# ============================================================================
echo ""
echo "Step 10: Creating directories..."
mkdir -p /var/www/smartcamera
mkdir -p /var/log/smartcamera
chown -R $SUDO_USER:$SUDO_USER /var/www/smartcamera 2>/dev/null || chown -R root:root /var/www/smartcamera
chown -R $SUDO_USER:$SUDO_USER /var/log/smartcamera 2>/dev/null || chown -R root:root /var/log/smartcamera

echo "✓ Directories created"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Installed Software:"
echo "  ✓ Python 3.11"
echo "  ✓ PostgreSQL (database: smartcamera_db)"
echo "  ✓ Redis (for WebSockets)"
echo "  ✓ Nginx (web server)"
echo "  ✓ Certbot (for SSL)"
echo "  ✓ Supervisor (process manager)"
echo "  ✓ All utilities"
echo ""
echo "Database Information:"
echo "  Database: smartcamera_db"
echo "  User: smartcamera"
echo "  Password: Saved to /root/db_password.txt"
echo ""
echo "Next Steps:"
echo "  1. Upload your code to /var/www/smartcamera"
echo "  2. Create .env file with database password"
echo "  3. Install Python packages: pip install -r requirements.txt"
echo "  4. Run migrations: python manage.py migrate"
echo "  5. Configure Nginx and start services"
echo ""
echo "=========================================="


