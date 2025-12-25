# Production Deployment Guide - Smart Mailbox

Complete guide for deploying Smart Mailbox to Hetzner Cloud with yourcamera.com domain, Let's Encrypt SSL, PostgreSQL, Redis, Nginx, and S3 backups.

## Prerequisites

1. **Hetzner Cloud Server**
   - Ubuntu 22.04 LTS
   - Minimum: 2 CPU, 4GB RAM, 20GB SSD
   - Recommended: 4 CPU, 8GB RAM, 40GB SSD

2. **Domain Name**
   - Domain: `yourcamera.com`
   - DNS access to configure A records

3. **AWS Account** (for S3 backups)
   - S3 bucket created
   - IAM user with S3 access

4. **Required Accounts**
   - SendGrid (for email) or SMTP server
   - Google Cloud (for Firebase Vision API)

## Step 1: Server Setup

### 1.1 Initial Server Configuration

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    docker.io \
    docker-compose \
    certbot \
    python3-certbot-nginx \
    awscli \
    git \
    curl \
    ufw

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (replace 'ubuntu' with your username)
sudo usermod -aG docker ubuntu
```

### 1.2 Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

## Step 2: DNS Configuration

Configure your domain DNS records:

```
Type    Name    Value           TTL
A       @       YOUR_HETZNER_IP 3600
A       www     YOUR_HETZNER_IP 3600
```

Replace `YOUR_HETZNER_IP` with your Hetzner server IP address.

Wait for DNS propagation (can take up to 48 hours, usually < 1 hour).

Verify DNS:
```bash
dig yourcamera.com
dig www.yourcamera.com
```

## Step 3: Clone and Configure Project

### 3.1 Clone Repository

```bash
cd /opt
sudo git clone <your-repo-url> smartmailbox
cd smartmailbox
sudo chown -R $USER:$USER .
```

### 3.2 Configure Environment

```bash
# Copy example environment file
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

**Required values to set:**
- `SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS` - `yourcamera.com,www.yourcamera.com`
- `DOMAIN` - `yourcamera.com`
- `POSTGRES_PASSWORD` - Strong password
- `SENDGRID_API_KEY` - Your SendGrid API key
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` - For backups
- `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` - For push notifications

### 3.3 Update Nginx Configuration

```bash
# Update domain in nginx config
sed -i 's/yourcamera.com/yourcamera.com/g' nginx/conf.d/yourcamera.com.conf
```

## Step 4: SSL Certificate Setup

### 4.1 Initial Certificate Request

```bash
# Make script executable
chmod +x scripts/setup-letsencrypt.sh

# Run SSL setup (replace with your email)
sudo ./scripts/setup-letsencrypt.sh yourcamera.com admin@yourcamera.com
```

### 4.2 Update Nginx to Use Certificates

The certificates will be in `/etc/letsencrypt/live/yourcamera.com/`

Update `nginx/conf.d/yourcamera.com.conf` to mount the certificates:

```yaml
# In docker-compose.prod.yml, nginx service volumes:
- /etc/letsencrypt:/etc/letsencrypt:ro
```

### 4.3 Auto-Renewal Setup

```bash
# Add to crontab
sudo crontab -e

# Add this line (runs on 1st of each month at midnight):
0 0 1 * * certbot renew --quiet --deploy-hook 'cd /opt/smartmailbox && docker-compose -f docker-compose.prod.yml restart nginx'
```

## Step 5: Deploy Application

### 5.1 Start Services

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5.2 Create Superuser

```bash
# Create Django admin user
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 5.3 Verify Deployment

1. **Check HTTP redirect**: `http://yourcamera.com` → should redirect to HTTPS
2. **Check HTTPS**: `https://yourcamera.com` → should show your app
3. **Check SSL**: Visit https://www.ssllabs.com/ssltest/analyze.html?d=yourcamera.com
4. **Check health**: `https://yourcamera.com/health/`

## Step 6: Configure S3 Backups

### 6.1 Create S3 Bucket

```bash
# Create bucket (replace region if needed)
aws s3 mb s3://smartmailbox-backups --region us-east-1

# Set lifecycle policy (optional - auto-delete old backups)
aws s3api put-bucket-lifecycle-configuration \
    --bucket smartmailbox-backups \
    --lifecycle-configuration file://s3-lifecycle.json
```

### 6.2 Setup Backup Script

```bash
# Make backup script executable
chmod +x scripts/backup-to-s3.sh

# Test backup manually
./scripts/backup-to-s3.sh
```

### 6.3 Schedule Daily Backups

```bash
# Add to crontab
crontab -e

# Add this line (runs daily at 2 AM):
0 2 * * * cd /opt/smartmailbox && ./scripts/backup-to-s3.sh >> /var/log/smartmailbox-backup.log 2>&1
```

## Step 7: Monitoring and Maintenance

### 7.1 View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 7.2 Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 7.3 Database Maintenance

```bash
# Access PostgreSQL
docker-compose -f docker-compose.prod.yml exec db psql -U smartmailbox_user smartmailbox

# Backup manually
docker-compose -f docker-compose.prod.yml exec db pg_dump -U smartmailbox_user smartmailbox > backup.sql
```

## Step 8: Security Checklist

- [ ] Firewall configured (only 22, 80, 443 open)
- [ ] Strong passwords set for all services
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Django `SECRET_KEY` is unique and secure
- [ ] Database password is strong
- [ ] Redis password set (if using)
- [ ] Environment variables not committed to git
- [ ] Regular backups configured
- [ ] Logs are being monitored
- [ ] Updates scheduled regularly

## Troubleshooting

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run

# Manually renew
sudo certbot renew
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test connection
docker-compose -f docker-compose.prod.yml exec db psql -U smartmailbox_user -d smartmailbox -c "SELECT 1;"
```

### Nginx Issues

```bash
# Test nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx
docker-compose -f docker-compose.prod.yml restart nginx

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### Backup Issues

```bash
# Test AWS credentials
aws s3 ls s3://smartmailbox-backups/

# Check backup script manually
./scripts/backup-to-s3.sh

# View backup logs
tail -f /var/log/smartmailbox-backup.log
```

## Backup and Restore

### Manual Backup

```bash
./scripts/backup-to-s3.sh
```

### Restore from Backup

```bash
# List available backups
aws s3 ls s3://smartmailbox-backups/backups/

# Restore specific backup
./scripts/restore-from-s3.sh 20240101_020000
```

## Performance Tuning

### PostgreSQL Tuning

The docker-compose.prod.yml includes optimized PostgreSQL settings. Adjust based on your server resources.

### Nginx Caching

Static files are cached for 30 days. Media files cached for 7 days.

### Redis Memory

Redis is configured with 256MB max memory and LRU eviction policy.

## Support

For issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Check health endpoints: `https://yourcamera.com/health/`
3. Review this guide's troubleshooting section

## Next Steps

1. Set up monitoring (e.g., UptimeRobot, Pingdom)
2. Configure log aggregation (optional)
3. Set up alerts for backups
4. Regular security updates
5. Performance monitoring







