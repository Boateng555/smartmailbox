#!/bin/bash
# Server Setup Commands - Run these on your Ubuntu server

# Step 1: Install required packages
apt update
apt install python3-venv python3-pip python-is-python3 -y

# Step 2: Navigate to project
cd /var/www/smartmailbox/django-webapp

# Step 3: Remove failed venv and create new one
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Step 4: Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Create .env file
cat > .env << 'EOF'
SECRET_KEY=CHANGE_THIS_TO_RANDOM_SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=194.164.59.137
DATABASE_URL=sqlite:///db.sqlite3

# Firebase (if using)
# FIREBASE_CREDENTIALS_PATH=/path/to/firebase-key.json

# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Server IP
SERVER_IP=194.164.59.137
EOF

# Step 6: Generate secret key
SECRET_KEY=$(python3 manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
sed -i "s/CHANGE_THIS_TO_RANDOM_SECRET_KEY/$SECRET_KEY/" .env

# Step 7: Run migrations
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py collectstatic --noinput

echo "Setup complete! Now you can run: python3 manage.py runserver 0.0.0.0:8000"

