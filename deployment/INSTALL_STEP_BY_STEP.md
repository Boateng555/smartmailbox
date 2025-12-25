# Step-by-Step Installation Commands

Copy and paste these commands one by one on your server: **194.164.59.137**

## Connect to Your Server First

```bash
ssh root@194.164.59.137
```

---

## Step 1: Update System

```bash
apt-get update
apt-get upgrade -y
```

---

## Step 2: Install Python 3.11

```bash
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 -m pip install --upgrade pip
```

**Verify:**
```bash
python3.11 --version
```

---

## Step 3: Install PostgreSQL (Database)

```bash
apt-get install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql
```

**Create Database:**
```bash
# Generate a random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Create database and user
sudo -u postgres psql << EOF
CREATE USER smartcamera WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE smartcamera_db OWNER smartcamera;
GRANT ALL PRIVILEGES ON DATABASE smartcamera_db TO smartcamera;
\q
EOF

# Save password
echo "DB_PASSWORD=$DB_PASSWORD" > /root/db_password.txt
chmod 600 /root/db_password.txt

# Show password
echo "Database password: $DB_PASSWORD"
```

**Verify:**
```bash
systemctl status postgresql
```

---

## Step 4: Install Redis (for WebSockets)

```bash
apt-get install -y redis-server
```

**Configure Redis:**
```bash
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
sed -i 's/^# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
```

**Start Redis:**
```bash
systemctl restart redis-server
systemctl enable redis-server
```

**Verify:**
```bash
systemctl status redis-server
```

---

## Step 5: Install Nginx (Web Server)

```bash
apt-get install -y nginx
systemctl start nginx
systemctl enable nginx
```

**Verify:**
```bash
systemctl status nginx
```

**Test in browser:** `http://194.164.59.137` (should show Nginx welcome page)

---

## Step 6: Install Certbot (for SSL)

```bash
apt-get install -y certbot python3-certbot-nginx
```

**Verify:**
```bash
certbot --version
```

---

## Step 7: Install Supervisor (Process Manager)

```bash
apt-get install -y supervisor
systemctl start supervisor
systemctl enable supervisor
```

**Verify:**
```bash
systemctl status supervisor
```

---

## Step 8: Install Utilities

```bash
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
```

---

## Step 9: Configure Firewall

```bash
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
```

**Check status:**
```bash
ufw status
```

---

## Step 10: Create Directories

```bash
mkdir -p /var/www/smartcamera
mkdir -p /var/log/smartcamera
chown -R root:root /var/www/smartcamera
chown -R root:root /var/log/smartcamera
```

---

## Verify Everything is Installed

```bash
echo "=== Installation Check ==="
echo "Python 3.11:"
python3.11 --version

echo ""
echo "PostgreSQL:"
systemctl status postgresql --no-pager | head -3

echo ""
echo "Redis:"
systemctl status redis-server --no-pager | head -3

echo ""
echo "Nginx:"
systemctl status nginx --no-pager | head -3

echo ""
echo "Supervisor:"
systemctl status supervisor --no-pager | head -3

echo ""
echo "Firewall:"
ufw status

echo ""
echo "Database Password:"
cat /root/db_password.txt
```

---

## Quick Install (All at Once)

If you want to install everything with one command:

```bash
# Make script executable
chmod +x /path/to/INSTALL_COMMANDS.sh

# Run it
bash /path/to/INSTALL_COMMANDS.sh
```

Or copy all commands into one file and run:

```bash
# Create install script
cat > /tmp/install_all.sh << 'SCRIPT'
# Paste all the commands from above here
SCRIPT

# Run it
bash /tmp/install_all.sh
```

---

## What You've Installed

✅ **Python 3.11** - Runs Django application  
✅ **PostgreSQL** - Database for storing photos and device data  
✅ **Redis** - Handles WebSocket connections  
✅ **Nginx** - Web server that serves your application  
✅ **Certbot** - For SSL certificates (HTTPS)  
✅ **Supervisor** - Keeps services running automatically  
✅ **Utilities** - Git, curl, build tools, etc.  

---

## Next Steps

1. **Upload your Django code** to `/var/www/smartcamera`
2. **Create .env file** with database password from `/root/db_password.txt`
3. **Install Python packages**: `pip install -r requirements.txt`
4. **Run migrations**: `python manage.py migrate`
5. **Configure Nginx** and start services

See `SERVER_SETUP_GUIDE.md` for detailed next steps!


