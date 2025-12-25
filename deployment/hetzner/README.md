# Hetzner CPX11 Deployment Files

Production deployment configuration for Smart Mailbox on Hetzner Cloud.

## Files

- **setup.sh** - Complete server setup script
- **ssl_setup.sh** - SSL certificate setup
- **monitoring.sh** - Monitoring tools setup
- **nginx.conf** - Nginx configuration template
- **supervisor.conf** - Supervisor configuration
- **DEPLOYMENT_GUIDE.md** - Complete deployment guide

## Quick Start

1. **Run Setup**
   ```bash
   sudo bash setup.sh yourcamera.com
   ```

2. **Configure DNS**
   - Point domain to Hetzner IP

3. **Setup SSL**
   ```bash
   sudo bash ssl_setup.sh yourcamera.com admin@yourcamera.com
   ```

4. **Deploy Application**
   ```bash
   sudo -u smartmailbox /opt/smartmailbox/deploy.sh
   ```

5. **Setup Monitoring**
   ```bash
   sudo bash monitoring.sh
   ```

## Server Specifications

- **Instance**: Hetzner CPX11
- **CPU**: 2 vCPU
- **RAM**: 4 GB
- **Storage**: 40 GB SSD
- **OS**: Ubuntu 22.04 LTS

## Services

- **Django**: Daphne (ASGI) on port 8001
- **Nginx**: Reverse proxy on ports 80/443
- **PostgreSQL**: Database on port 5432
- **Redis**: Cache/Channels on port 6379
- **Supervisor**: Process management

## Directory Structure

```
/opt/smartmailbox/
├── django-webapp/          # Django application
├── venv/                   # Python virtual environment
├── static/                 # Static files
├── media/                  # Media files
├── logs/                   # Application logs
├── backups/                # Backup files
├── .env.production         # Environment variables
├── deploy.sh               # Deployment script
├── backup.sh               # Backup script
└── monitor.sh              # Monitoring script
```

## Configuration

All configuration is in `/opt/smartmailbox/.env.production`

See `DEPLOYMENT_GUIDE.md` for complete setup instructions.







