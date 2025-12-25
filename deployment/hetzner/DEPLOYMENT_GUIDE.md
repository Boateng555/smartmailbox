# Hetzner CPX11 Production Deployment Guide

Complete guide for deploying Smart Mailbox to Hetzner CPX11 server.

## Prerequisites

1. **Hetzner Cloud Account**
   - Create account at [Hetzner Cloud](https://www.hetzner.com/cloud)
   - Create CPX11 server (Ubuntu 22.04 LTS)
   - Note server IP address

2. **Domain Name**
   - Domain registered (e.g., yourcamera.com)
   - DNS access to configure A records

3. **AWS Account** (for S3 backups)
   - S3 bucket created
   - IAM user with S3 access

## Step 1: Server Setup

### 1.1 Connect to Server

```bash
ssh root@YOUR_HETZNER_IP
```

### 1.2 Run Setup Script

```bash
# Download setup script
wget https://raw.githubusercontent.com/your-repo/deployment/hetzner/setup.sh
# Or copy from your local machine
scp deployment/hetzner/setup.sh root@YOUR_HETZNER_IP:/root/

# Run setup
sudo bash setup.sh yourcamera.com
```

The script will:
- Update system packages
- Install Python 3.11, PostgreSQL, Redis, Nginx
- Configure firewall
- Setup application user and directories
- Configure databases
- Setup Nginx and Supervisor
- Create backup scripts

**Important**: Save the generated passwords (database, Redis) shown at the end!

## Step 2: DNS Configuration

### 2.1 Configure DNS Records

Point your domain to the Hetzner server:

```
Type    Name    Value           TTL
A       @       YOUR_HETZNER_IP 3600
A       www     YOUR_HETZNER_IP 3600
```

### 2.2 Verify DNS

```bash
dig yourcamera.com
dig www.yourcamera.com
```

Wait for DNS propagation (usually < 1 hour, can take up to 48 hours).

## Step 3: SSL Certificate Setup

### 3.1 Obtain SSL Certificate

```bash
# Run SSL setup script
sudo bash ssl_setup.sh yourcamera.com admin@yourcamera.com
```

Or manually:

```bash
certbot --nginx -d yourcamera.com -d www.yourcamera.com
```

### 3.2 Verify SSL

Visit: https://www.ssllabs.com/ssltest/analyze.html?d=yourcamera.com

## Step 4: Deploy Application

### 4.1 Clone Repository

```bash
# Switch to application user
sudo su - smartmailbox

# Clone repository
cd /opt/smartmailbox
git clone YOUR_REPO_URL django-webapp
cd django-webapp
```

### 4.2 Configure Environment

```bash
# Edit environment file
nano /opt/smartmailbox/.env.production
```

Update with your values:
- Email configuration (SendGrid/SMTP)
- AWS S3 credentials for backups
- Firebase Vision API credentials
- Twilio credentials (if using SMS)

### 4.3 Install Dependencies

```bash
# Activate virtual environment
source /opt/smartmailbox/venv/bin/activate

# Install dependencies
cd /opt/smartmailbox/django-webapp
pip install -r requirements.txt
```

### 4.4 Run Migrations

```bash
# Set environment
export DJANGO_SETTINGS_MODULE=iot_platform.settings_production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 4.5 Start Application

```bash
# Start with Supervisor
sudo supervisorctl start smartmailbox

# Check status
sudo supervisorctl status smartmailbox

# View logs
tail -f /opt/smartmailbox/logs/daphne.log
```

## Step 5: Setup Monitoring

### 5.1 Install Monitoring Tools

```bash
sudo bash monitoring.sh
```

### 5.2 Configure Uptime Monitoring

Use external service (UptimeRobot, Pingdom, etc.):
- URL: `https://yourcamera.com/health/`
- Interval: 5 minutes
- Alert: Email/SMS on failure

## Step 6: Verify Deployment

### 6.1 Check Services

```bash
# Check Nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql

# Check Redis
sudo systemctl status redis-server

# Check Supervisor
sudo supervisorctl status
```

### 6.2 Test Endpoints

```bash
# Health check
curl https://yourcamera.com/health/

# API endpoint
curl https://yourcamera.com/api/device/heartbeat/

# Dashboard
curl -I https://yourcamera.com/dashboard/
```

## Step 7: Backup Configuration

### 7.1 Configure S3 Backup

Edit `/opt/smartmailbox/.env.production`:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=smartmailbox-backups
```

### 7.2 Test Backup

```bash
sudo -u smartmailbox /opt/smartmailbox/backup.sh
```

### 7.3 Verify Backup Schedule

```bash
sudo -u smartmailbox crontab -l
# Should show: 0 2 * * * /opt/smartmailbox/backup.sh
```

## Step 8: Ongoing Maintenance

### 8.1 Update Application

```bash
sudo -u smartmailbox /opt/smartmailbox/deploy.sh
```

Or manually:

```bash
sudo su - smartmailbox
cd /opt/smartmailbox/django-webapp
git pull
source /opt/smartmailbox/venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
exit
sudo supervisorctl restart smartmailbox
```

### 8.2 View Logs

```bash
# Application logs
tail -f /opt/smartmailbox/logs/daphne.log

# Nginx logs
tail -f /var/log/nginx/smartmailbox-access.log
tail -f /var/log/nginx/smartmailbox-error.log

# System monitoring
tail -f /opt/smartmailbox/logs/monitoring.log
```

### 8.3 Restart Services

```bash
# Restart Django
sudo supervisorctl restart smartmailbox

# Restart Nginx
sudo systemctl restart nginx

# Restart all
sudo supervisorctl restart all
```

## Troubleshooting

### Issue: SSL Certificate Not Working

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Issue: Django Not Starting

```bash
# Check logs
tail -f /opt/smartmailbox/logs/daphne_error.log

# Check environment
sudo -u smartmailbox /opt/smartmailbox/venv/bin/python /opt/smartmailbox/django-webapp/manage.py check

# Check database connection
sudo -u postgres psql -d smartmailbox -c "SELECT 1;"
```

### Issue: High Memory Usage

```bash
# Check memory
free -h

# Check processes
htop

# Restart services
sudo supervisorctl restart smartmailbox
```

### Issue: Backup Failing

```bash
# Test AWS credentials
aws s3 ls s3://smartmailbox-backups/

# Check backup script
sudo -u smartmailbox /opt/smartmailbox/backup.sh

# Check logs
tail -f /opt/smartmailbox/logs/backup.log
```

## Security Checklist

- [ ] Firewall configured (only 22, 80, 443 open)
- [ ] Fail2ban enabled
- [ ] Strong passwords set
- [ ] SSL certificate installed
- [ ] Auto-renewal configured
- [ ] Database password secure
- [ ] Redis password set
- [ ] Environment variables not exposed
- [ ] Regular backups configured
- [ ] Monitoring enabled

## Performance Optimization

### PostgreSQL Tuning

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Nginx Optimization

Already configured in nginx.conf:
- Gzip compression
- Static file caching
- Keepalive connections
- Client timeouts

## Monitoring Endpoints

- **Health Check**: `https://yourcamera.com/health/`
- **API Status**: `https://yourcamera.com/api/device/heartbeat/`
- **Dashboard**: `https://yourcamera.com/dashboard/`

## Backup and Restore

### Manual Backup

```bash
sudo -u smartmailbox /opt/smartmailbox/backup.sh
```

### Restore from Backup

```bash
# Restore database
gunzip < backup.sql.gz | sudo -u postgres psql smartmailbox

# Restore media
tar xzf media_backup.tar.gz -C /opt/smartmailbox/
```

## Support

For issues:
1. Check logs: `/opt/smartmailbox/logs/`
2. Check service status: `sudo supervisorctl status`
3. Review this guide's troubleshooting section
4. Check Hetzner Cloud console for server status

## Next Steps

1. Set up external monitoring (UptimeRobot, etc.)
2. Configure email notifications
3. Set up SMS notifications (Twilio)
4. Configure Firebase Vision API
5. Test complete mail detection flow
6. Monitor performance and adjust







