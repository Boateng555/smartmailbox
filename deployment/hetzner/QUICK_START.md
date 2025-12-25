# Quick Start - Hetzner CPX11 Deployment

## 5-Minute Setup

### 1. Server Setup (5 minutes)

```bash
# SSH to your Hetzner server
ssh root@YOUR_HETZNER_IP

# Download and run setup script
wget https://raw.githubusercontent.com/your-repo/deployment/hetzner/setup.sh
sudo bash setup.sh yourcamera.com

# Save the passwords shown at the end!
```

### 2. DNS Configuration (1 minute)

Point your domain DNS:
- `A` record: `@` → `YOUR_HETZNER_IP`
- `A` record: `www` → `YOUR_HETZNER_IP`

Wait for DNS propagation (check: `dig yourcamera.com`)

### 3. SSL Certificate (2 minutes)

```bash
sudo bash ssl_setup.sh yourcamera.com admin@yourcamera.com
```

### 4. Deploy Application (5 minutes)

```bash
# Switch to app user
sudo su - smartmailbox

# Clone repository
cd /opt/smartmailbox
git clone YOUR_REPO_URL django-webapp
cd django-webapp

# Install and setup
source /opt/smartmailbox/venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=iot_platform.settings_production
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput

# Exit and start service
exit
sudo supervisorctl start smartmailbox
```

### 5. Verify (1 minute)

```bash
# Check services
sudo supervisorctl status
curl https://yourcamera.com/health/

# View logs
tail -f /opt/smartmailbox/logs/daphne.log
```

## Total Time: ~15 minutes

## Next Steps

1. Configure email (SendGrid/SMTP) in `.env.production`
2. Setup S3 backups (AWS credentials)
3. Configure Firebase Vision API
4. Setup monitoring (external service)

See `DEPLOYMENT_GUIDE.md` for detailed instructions.







