# Server Setup - Fix Commands

Run these commands on your server to fix the issues:

## Step 1: Install Required Packages

```bash
apt update
apt install python3-venv python3-pip python-is-python3 -y
```

## Step 2: Fix Requirements.txt

The `sendgrid-django>=5.3.0` doesn't exist. Edit requirements.txt:

```bash
cd /var/www/smartmailbox/django-webapp
nano requirements.txt
```

Change line with `sendgrid-django>=5.3.0` to:
```
sendgrid-django>=4.2.0
```

Or remove it if you're not using SendGrid.

## Step 3: Create Virtual Environment

```bash
cd /var/www/smartmailbox/django-webapp
rm -rf venv  # Remove failed venv
python3 -m venv venv
source venv/bin/activate
```

## Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 5: Create .env File

Since .env.example doesn't exist, create .env manually:

```bash
cd /var/www/smartmailbox/django-webapp
nano .env
```

Add these variables:
```
SECRET_KEY=your-secret-key-here-generate-with-django
DEBUG=False
ALLOWED_HOSTS=194.164.59.137,your-domain.com
DATABASE_URL=sqlite:///db.sqlite3

# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/mailbox_db
```

## Step 6: Generate Secret Key

```bash
python3 manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and add it to .env as SECRET_KEY.

## Step 7: Run Migrations

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py collectstatic --noinput
```

