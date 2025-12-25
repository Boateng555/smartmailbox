# Quick Server Setup Guide

## Issues Fixed:
1. ✅ `sendgrid-django` version updated (5.3.0 → 4.2.0)
2. ✅ Instructions for installing `python3-venv`
3. ✅ Instructions for creating `.env` file

## Run These Commands on Your Server:

### Step 1: Install Required Packages
```bash
apt update
apt install python3-venv python3-pip python-is-python3 -y
```

### Step 2: Pull Latest Code (with fixes)
```bash
cd /var/www/smartmailbox
git pull origin main
cd django-webapp
```

### Step 3: Create Virtual Environment
```bash
rm -rf venv  # Remove failed venv
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Create .env File
```bash
nano .env
```

Paste this content (edit as needed):
```env
SECRET_KEY=generate-this-below
DEBUG=False
ALLOWED_HOSTS=194.164.59.137
DATABASE_URL=sqlite:///db.sqlite3

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Server IP
SERVER_IP=194.164.59.137
```

### Step 6: Generate Secret Key
```bash
python3 manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and replace `generate-this-below` in `.env` file.

### Step 7: Run Migrations
```bash
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py collectstatic --noinput
```

### Step 8: Test Server
```bash
python3 manage.py runserver 0.0.0.0:8000
```

Visit: `http://194.164.59.137:8000`

## Or Use the Automated Script:

```bash
cd /var/www/smartmailbox
git pull origin main
chmod +x SERVER_SETUP_COMMANDS.sh
./SERVER_SETUP_COMMANDS.sh
```

## Next Steps After Setup:

1. **Setup Nginx** (reverse proxy)
2. **Setup Supervisor** (process manager)
3. **Setup SSL** (optional but recommended)

See `DEPLOYMENT_GUIDE.md` for complete instructions.

