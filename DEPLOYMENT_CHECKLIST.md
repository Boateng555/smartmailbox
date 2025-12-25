# Production Deployment Checklist

## Pre-Deployment

### Server Setup
- [ ] Hetzner Cloud server created (Ubuntu 22.04)
- [ ] Server IP noted: `_____________`
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] Docker and Docker Compose installed
- [ ] Certbot installed
- [ ] AWS CLI installed

### Domain Configuration
- [ ] Domain `yourcamera.com` registered
- [ ] DNS A record: `@` → Server IP
- [ ] DNS A record: `www` → Server IP
- [ ] DNS propagation verified (`dig yourcamera.com`)

### Service Accounts
- [ ] SendGrid account created, API key obtained
- [ ] Google Cloud account, Firebase Vision API enabled
- [ ] AWS account, S3 bucket created
- [ ] AWS IAM user with S3 access, credentials obtained

## Configuration

### Environment Variables
- [ ] `.env.production` created from example
- [ ] `SECRET_KEY` generated and set
- [ ] `ALLOWED_HOSTS` set to `yourcamera.com,www.yourcamera.com`
- [ ] `DOMAIN` set to `yourcamera.com`
- [ ] `POSTGRES_PASSWORD` set (strong password)
- [ ] `SENDGRID_API_KEY` set
- [ ] `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` set
- [ ] `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` generated and set
- [ ] `GOOGLE_APPLICATION_CREDENTIALS` path set (if using Firebase)

### Nginx Configuration
- [ ] `nginx/conf.d/yourcamera.com.conf` updated with domain
- [ ] SSL certificate paths verified

## Deployment

### SSL Certificate
- [ ] Let's Encrypt certificate obtained
- [ ] Certificate auto-renewal configured (crontab)
- [ ] SSL test passed: https://www.ssllabs.com/ssltest/

### Application Deployment
- [ ] Code cloned to server
- [ ] Docker images built
- [ ] Services started (`docker-compose -f docker-compose.prod.yml up -d`)
- [ ] Database migrations run
- [ ] Static files collected
- [ ] Superuser created
- [ ] Application accessible at https://yourcamera.com

### Backups
- [ ] S3 bucket created and accessible
- [ ] Backup script tested manually
- [ ] Daily backup cron job configured
- [ ] Backup restoration tested

## Post-Deployment Verification

### Functionality Tests
- [ ] HTTPS redirect working (HTTP → HTTPS)
- [ ] Homepage loads correctly
- [ ] Login page accessible
- [ ] Dashboard loads
- [ ] WebSocket connections work
- [ ] API endpoints respond
- [ ] Static files served correctly
- [ ] Media files accessible

### Security Checks
- [ ] SSL certificate valid (A+ rating on SSL Labs)
- [ ] Security headers present
- [ ] Firewall configured correctly
- [ ] No sensitive data in logs
- [ ] Environment variables not exposed

### Performance Checks
- [ ] Page load times acceptable
- [ ] Database queries optimized
- [ ] Redis caching working
- [ ] Image uploads working

## Monitoring Setup

- [ ] Log monitoring configured
- [ ] Uptime monitoring set up (optional)
- [ ] Backup success notifications configured
- [ ] Error alerting set up (optional)

## Documentation

- [ ] Server access documented
- [ ] Backup restoration procedure documented
- [ ] Update procedure documented
- [ ] Emergency contacts listed

## Maintenance Schedule

- [ ] Weekly: Review logs
- [ ] Monthly: SSL certificate renewal check
- [ ] Monthly: Security updates
- [ ] Quarterly: Backup restoration test
- [ ] Quarterly: Performance review

## Emergency Contacts

- Server Provider: Hetzner Support
- Domain Registrar: _____________
- AWS Support: _____________
- Team Contacts: _____________

## Quick Reference

**Server Location:** `/opt/smartmailbox`

**Key Commands:**
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Run backup
./scripts/backup-to-s3.sh

# Deploy updates
./scripts/deploy.sh
```

**Important Files:**
- `.env.production` - Environment configuration
- `docker-compose.prod.yml` - Service definitions
- `nginx/conf.d/yourcamera.com.conf` - Nginx config
- `/etc/letsencrypt/live/yourcamera.com/` - SSL certificates







