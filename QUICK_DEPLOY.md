# Quick Deployment Guide - Smart Mailbox

Quick reference for deploying to Hetzner Cloud with yourcamera.com.

## Prerequisites Checklist

- [ ] Hetzner Cloud server (Ubuntu 22.04)
- [ ] Domain `yourcamera.com` DNS pointing to server IP
- [ ] AWS account with S3 bucket created
- [ ] SendGrid account (or SMTP credentials)
- [ ] Google Cloud account (for Firebase Vision)

## Quick Start (5 Steps)

### 1. Server Setup

```bash
# On Hetzner server
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y docker.io docker-compose certbot python3-certbot-nginx awscli git
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker  # Or logout/login
```

### 2. Clone & Configure

```bash
cd /opt
sudo git clone <your-repo> smartmailbox
cd smartmailbox
sudo chown -R $USER:$USER .

# Copy and edit environment
cp .env.production.example .env.production
nano .env.production  # Fill in all values
```

### 3. SSL Certificate

```bash
# Update domain in nginx config
sed -i 's/yourcamera.com/yourcamera.com/g' nginx/conf.d/yourcamera.com.conf

# Get SSL certificate
chmod +x scripts/setup-letsencrypt.sh
sudo ./scripts/setup-letsencrypt.sh yourcamera.com admin@yourcamera.com
```

### 4. Deploy

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 5. Setup Backups

```bash
chmod +x scripts/backup-to-s3.sh

# Test backup
./scripts/backup-to-s3.sh

# Schedule daily backups (2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/smartmailbox && ./scripts/backup-to-s3.sh >> /var/log/smartmailbox-backup.log 2>&1") | crontab -
```

## Verify Deployment

```bash
# Check services
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test HTTPS
curl -I https://yourcamera.com
```

## Common Commands

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Restart service
docker-compose -f docker-compose.prod.yml restart web

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Backup manually
./scripts/backup-to-s3.sh

# Update application
git pull && ./scripts/deploy.sh
```

## Environment Variables Required

See `.env.production.example` for all required variables.

**Critical ones:**
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - yourcamera.com,www.yourcamera.com
- `POSTGRES_PASSWORD` - Database password
- `SENDGRID_API_KEY` - Email service
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - For backups

## Troubleshooting

**SSL not working?**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

**Database connection error?**
```bash
docker-compose -f docker-compose.prod.yml logs db
docker-compose -f docker-compose.prod.yml exec db psql -U smartmailbox_user -d smartmailbox
```

**Nginx errors?**
```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
docker-compose -f docker-compose.prod.yml logs nginx
```

## Full Documentation

See `PRODUCTION_DEPLOYMENT.md` for complete guide.







