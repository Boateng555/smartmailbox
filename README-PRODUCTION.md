# Smart Mailbox - Production Deployment

Complete production deployment setup for Smart Mailbox on Hetzner Cloud.

## Architecture

```
Internet
   ↓
Nginx (Port 80/443) - SSL/TLS termination, reverse proxy
   ↓
Django + Daphne (Port 8001) - ASGI application
   ↓
PostgreSQL (Port 5432) - Database
   ↓
Redis (Port 6379) - Cache & WebSocket channels
```

## Quick Start

1. **Setup Server** (see `PRODUCTION_DEPLOYMENT.md`)
2. **Configure Domain** (DNS → Hetzner IP)
3. **Get SSL Certificate** (`./scripts/setup-letsencrypt.sh`)
4. **Deploy** (`./scripts/deploy.sh`)
5. **Setup Backups** (cron job for `./scripts/backup-to-s3.sh`)

## Files Overview

### Docker Compose
- `docker-compose.prod.yml` - Production services (Django, PostgreSQL, Redis, Nginx)

### Nginx
- `nginx/nginx.conf` - Main Nginx configuration
- `nginx/conf.d/yourcamera.com.conf` - Domain-specific config with SSL

### Scripts
- `scripts/setup-letsencrypt.sh` - SSL certificate setup
- `scripts/backup-to-s3.sh` - Daily backup to S3
- `scripts/restore-from-s3.sh` - Restore from backup
- `scripts/deploy.sh` - Full deployment script

### Configuration
- `.env.production.example` - Environment variables template
- `s3-lifecycle.json` - S3 backup retention policy

### Documentation
- `PRODUCTION_DEPLOYMENT.md` - Complete deployment guide
- `QUICK_DEPLOY.md` - Quick reference
- `DEPLOYMENT_CHECKLIST.md` - Pre-deployment checklist

## Services

### Web (Django)
- **Port**: 8001 (internal)
- **Framework**: Django 5.1 + Daphne (ASGI)
- **Features**: Web app, API, WebSocket support

### Database (PostgreSQL)
- **Port**: 5432 (internal only)
- **Version**: PostgreSQL 15
- **Optimized**: Production settings included

### Cache (Redis)
- **Port**: 6379 (internal only)
- **Version**: Redis 7
- **Features**: Caching, WebSocket channels

### Web Server (Nginx)
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Features**: SSL termination, reverse proxy, static files

## SSL Certificate

- **Provider**: Let's Encrypt (free)
- **Auto-renewal**: Configured via cron
- **Location**: `/etc/letsencrypt/live/yourcamera.com/`

## Backups

- **Frequency**: Daily at 2 AM
- **Destination**: AWS S3
- **Retention**: 30 days (configurable)
- **Contents**: Database, media files, configuration

## Security Features

- ✅ HTTPS enforced (HTTP → HTTPS redirect)
- ✅ Security headers (HSTS, XSS protection, etc.)
- ✅ Firewall configured
- ✅ Database and Redis not exposed externally
- ✅ Strong password requirements
- ✅ Environment variables for secrets

## Monitoring

- Logs: `docker-compose -f docker-compose.prod.yml logs`
- Health: `https://yourcamera.com/health/`
- SSL: https://www.ssllabs.com/ssltest/

## Support

For detailed instructions, see:
- `PRODUCTION_DEPLOYMENT.md` - Full deployment guide
- `QUICK_DEPLOY.md` - Quick reference
- `DEPLOYMENT_CHECKLIST.md` - Pre-deployment checklist
