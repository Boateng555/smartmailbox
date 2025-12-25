#!/bin/bash
# Monitoring setup script
# Usage: sudo bash monitoring.sh

set -e

if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root or with sudo"
    exit 1
fi

echo "=========================================="
echo "Monitoring Setup"
echo "=========================================="
echo ""

# Install monitoring tools
apt-get update
apt-get install -y \
    htop \
    iotop \
    netstat-nat \
    nethogs \
    logwatch \
    unattended-upgrades

# Setup logwatch
echo "Configuring logwatch..."
cat > /etc/logwatch/conf/logwatch.conf <<EOF
LogDir = /var/log
TmpDir = /var/cache/logwatch
MailTo = root
MailFrom = logwatch@yourcamera.com
Print = No
Save = /var/log/logwatch
Range = yesterday
Detail = Med
Service = All
Format = html
Encode = none
EOF

# Create monitoring script
cat > /opt/smartmailbox/monitor.sh <<'MONITOR_SCRIPT'
#!/bin/bash
# System monitoring script
APP_DIR="/opt/smartmailbox"
LOG_FILE="$APP_DIR/logs/monitoring.log"

{
    echo "=== $(date) ==="
    echo "Uptime: $(uptime)"
    echo "Disk Usage:"
    df -h | grep -E '^/dev/'
    echo ""
    echo "Memory Usage:"
    free -h
    echo ""
    echo "Django Process:"
    supervisorctl status smartmailbox
    echo ""
    echo "Recent Errors:"
    tail -n 20 $APP_DIR/logs/daphne_error.log 2>/dev/null || echo "No error log"
    echo ""
} >> $LOG_FILE

# Keep only last 30 days
find $APP_DIR/logs -name "monitoring.log" -mtime +30 -delete
MONITOR_SCRIPT

chmod +x /opt/smartmailbox/monitor.sh
chown smartmailbox:smartmailbox /opt/smartmailbox/monitor.sh

# Setup monitoring cron (every hour)
(crontab -u smartmailbox -l 2>/dev/null; echo "0 * * * * /opt/smartmailbox/monitor.sh") | crontab -u smartmailbox -

# Create health check endpoint script
cat > /opt/smartmailbox/health_check.sh <<'HEALTH_SCRIPT'
#!/bin/bash
# Health check script for uptime monitoring
APP_DIR="/opt/smartmailbox"
DOMAIN=${1:-"yourcamera.com"}

# Check if Django is responding
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health/ || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
    echo "Health check failed: HTTP $HTTP_CODE"
    # Restart Django
    supervisorctl restart smartmailbox
    exit 1
fi

echo "Health check passed: HTTP $HTTP_CODE"
exit 0
HEALTH_SCRIPT

chmod +x /opt/smartmailbox/health_check.sh
chown smartmailbox:smartmailbox /opt/smartmailbox/health_check.sh

# Setup health check cron (every 5 minutes)
(crontab -u smartmailbox -l 2>/dev/null; echo "*/5 * * * * /opt/smartmailbox/health_check.sh >> /opt/smartmailbox/logs/health_check.log 2>&1") | crontab -u smartmailbox -

echo ""
echo "Monitoring setup completed!"
echo ""
echo "Monitoring tools installed:"
echo "- htop: System monitor"
echo "- logwatch: Log analysis"
echo "- Health check: Every 5 minutes"
echo "- System monitoring: Every hour"
echo ""
echo "View logs:"
echo "- Monitoring: /opt/smartmailbox/logs/monitoring.log"
echo "- Health checks: /opt/smartmailbox/logs/health_check.log"
echo ""







