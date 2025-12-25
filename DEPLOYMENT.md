# Production Deployment Guide

Complete guide for deploying the IoT Platform to production.

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your production values

# 2. Generate self-signed cert (temporary, for initial setup)
bash scripts/generate-selfsigned-cert.sh yourdomain.com

# 3. Configure firewall
sudo bash scripts/setup-firewall.sh

# 4. Start services
docker-compose up -d

# 5. Initialize database
bash scripts/init-db.sh

# 6. Setup Let's Encrypt SSL (replace self-signed)
sudo bash scripts/setup-ssl.sh yourdomain.com admin@yourdomain.com

# 7. Restart nginx
docker-compose restart nginx
```

## Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Required variables:
- `SECRET_KEY` - Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG=False`
- `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
- `POSTGRES_PASSWORD` - Strong password
- `MQTT_PASSWORD` - If using MQTT

## Services

### Web (Django + Daphne)
- **Port**: 8001 (internal), 8000 (dev access)
- **ASGI Server**: Daphne
- **Features**: HTTP, WebSocket, REST API

### Database (PostgreSQL)
- **Port**: 5432
- **Version**: PostgreSQL 15
- **Data**: Persisted in `postgres_data` volume

### Redis
- **Port**: 6379
- **Purpose**: Channels WebSocket backend
- **Data**: Persisted in `redis_data` volume

### Nginx
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Purpose**: Reverse proxy, SSL termination, static files

## SSL Certificate Setup

### Option 1: Let's Encrypt (Recommended)

```bash
sudo bash scripts/setup-ssl.sh yourdomain.com admin@yourdomain.com
```

### Option 2: Self-Signed (Development)

```bash
bash scripts/generate-selfsigned-cert.sh localhost
```

### Auto-Renewal

Add to crontab:
```bash
0 0 1 * * certbot renew --quiet && docker-compose restart nginx
```

## Firewall Configuration

### Automatic (Recommended)
```bash
sudo bash scripts/setup-firewall.sh
```

### Manual
See `scripts/firewall-guide.md` for detailed instructions.

**Required Ports:**
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8000 (Development, optional)

## Database Management

### Backup
```bash
docker-compose exec db pg_dump -U iot_user iot_platform > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
docker-compose exec -T db psql -U iot_user iot_platform < backup_YYYYMMDD.sql
```

### Access Database
```bash
docker-compose exec db psql -U iot_user iot_platform
```

## Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db

# Django logs
docker-compose exec web tail -f /app/logs/django.log
```

### Check Status
```bash
docker-compose ps
docker-compose exec web python manage.py check
```

## Maintenance

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build web

# Run migrations
docker-compose exec web python manage.py migrate
```

### Update Dependencies
```bash
# Edit requirements.txt
# Rebuild
docker-compose build web
docker-compose up -d web
```

## Security Checklist

- [ ] Changed SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configured ALLOWED_HOSTS
- [ ] Strong database password
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Regular backups scheduled
- [ ] Logs directory permissions set
- [ ] Media directory permissions set

## Troubleshooting

### Services won't start
- Check `.env` file exists
- Verify ports aren't in use
- Check Docker logs: `docker-compose logs`

### Database connection errors
- Verify DATABASE_URL in .env
- Check database is healthy: `docker-compose ps db`
- Check database logs: `docker-compose logs db`

### SSL certificate issues
- Ensure domain DNS points to server
- Verify port 80 is accessible
- Check certificate files exist: `ls nginx/ssl/`

### Static files not loading
- Run collectstatic: `docker-compose exec web python manage.py collectstatic --noinput`
- Check nginx static volume mount
- Verify static files in container: `docker-compose exec web ls -la /app/staticfiles`

## Production Best Practices

1. **Use environment variables** for all secrets
2. **Enable HTTPS only** - redirect HTTP to HTTPS
3. **Regular backups** - automate database backups
4. **Monitor logs** - set up log rotation
5. **Update regularly** - keep dependencies updated
6. **Use strong passwords** - for all services
7. **Restrict access** - use firewall rules
8. **Monitor resources** - CPU, memory, disk usage







