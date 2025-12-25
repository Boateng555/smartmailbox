# First Time Server Setup - Getting Your Code on the Server

## Step 1: Create Directory Structure

On your server, run:

```bash
mkdir -p /var/www/smartcamera
cd /var/www/smartcamera
```

## Step 2: Upload Your Code

You have 3 options:

### Option A: Using SCP (from your local computer)

On your **local computer** (Windows/Mac/Linux), run:

```bash
# Upload entire project
scp -r esp32-cam-product root@194.164.59.137:/var/www/smartcamera/

# Or just upload the deployment folder first
scp -r deployment root@194.164.59.137:/var/www/smartcamera/
```

### Option B: Using Git (if you have a repository)

On your **server**, run:

```bash
cd /var/www/smartcamera
git clone YOUR_REPO_URL .
```

### Option C: Manual Upload (using SFTP client)

1. Use FileZilla, WinSCP, or similar SFTP client
2. Connect to: `194.164.59.137` as `root`
3. Upload your `esp32-cam-product` folder to `/var/www/smartcamera/`

## Step 3: After Uploading, Run Setup

```bash
cd /var/www/smartcamera/deployment
chmod +x QUICK_SETUP.sh
bash QUICK_SETUP.sh
```

---

## Quick Alternative: Install Software First, Then Upload Code

If you want to install software first (before uploading code):

### Step 1: Install All Software

Run these commands on your server:

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.11
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip
python3.11 -m pip install --upgrade pip

# Install PostgreSQL
apt-get install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql

# Create database
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
sudo -u postgres psql << EOF
CREATE USER smartcamera WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE smartcamera_db OWNER smartcamera;
GRANT ALL PRIVILEGES ON DATABASE smartcamera_db TO smartcamera;
\q
EOF
echo "DB_PASSWORD=$DB_PASSWORD" > /root/db_password.txt
chmod 600 /root/db_password.txt
echo "Database password: $DB_PASSWORD"

# Install Redis
apt-get install -y redis-server
sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# Install Nginx
apt-get install -y nginx
systemctl start nginx
systemctl enable nginx

# Install Certbot
apt-get install -y certbot python3-certbot-nginx

# Install Supervisor
apt-get install -y supervisor
systemctl start supervisor
systemctl enable supervisor

# Install utilities
apt-get install -y git curl wget htop ufw build-essential libpq-dev libssl-dev libffi-dev

# Configure firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp

# Create directories
mkdir -p /var/www/smartcamera
mkdir -p /var/log/smartcamera

echo "Software installation complete!"
echo "Database password saved to: /root/db_password.txt"
```

### Step 2: Upload Your Code

Then upload your code using one of the methods above (SCP, Git, or SFTP).

### Step 3: Run Django Setup

After uploading code:

```bash
cd /var/www/smartcamera/django-webapp
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Recommended: Install Software First

I recommend installing the software first (using the commands above), then uploading your code. This way you can verify everything is installed correctly before setting up Django.


