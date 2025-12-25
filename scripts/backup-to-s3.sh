#!/bin/bash
# Daily Backup Script for Smart Mailbox to AWS S3
# Usage: Run via cron daily
# Crontab: 0 2 * * * /path/to/backup-to-s3.sh

set -e

# Configuration
BACKUP_DIR="/tmp/smartmailbox_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET=${S3_BUCKET:-"smartmailbox-backups"}
S3_PREFIX=${S3_PREFIX:-"backups"}
RETENTION_DAYS=${RETENTION_DAYS:-30}

# AWS Configuration (from environment variables)
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-"us-east-1"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================="
echo "Smart Mailbox Backup to S3"
echo "==========================================${NC}"
echo "Timestamp: $TIMESTAMP"
echo "S3 Bucket: s3://$S3_BUCKET/$S3_PREFIX"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not installed${NC}"
    echo "Install with: apt-get install awscli"
    exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}ERROR: AWS credentials not set${NC}"
    echo "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

# Backup PostgreSQL database
echo -e "${YELLOW}Backing up PostgreSQL database...${NC}"
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U smartmailbox_user smartmailbox | gzip > "db_backup_${TIMESTAMP}.sql.gz"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database backup created${NC}"
else
    echo -e "${RED}✗ Database backup failed${NC}"
    exit 1
fi

# Backup media files
echo -e "${YELLOW}Backing up media files...${NC}"
docker-compose -f docker-compose.prod.yml exec -T web tar czf - /app/media > "media_backup_${TIMESTAMP}.tar.gz" 2>/dev/null || true

if [ -f "media_backup_${TIMESTAMP}.tar.gz" ]; then
    echo -e "${GREEN}✓ Media backup created${NC}"
else
    echo -e "${YELLOW}⚠ Media backup skipped (no media files)${NC}"
fi

# Backup static files (optional)
echo -e "${YELLOW}Backing up static files...${NC}"
docker-compose -f docker-compose.prod.yml exec -T web tar czf - /app/staticfiles > "static_backup_${TIMESTAMP}.tar.gz" 2>/dev/null || true

# Backup environment configuration (without secrets)
echo -e "${YELLOW}Backing up configuration...${NC}"
if [ -f "../.env.production" ]; then
    # Create a sanitized version (remove passwords)
    grep -v -E "(PASSWORD|SECRET|KEY)" ../.env.production > "config_backup_${TIMESTAMP}.txt" 2>/dev/null || true
    echo -e "${GREEN}✓ Configuration backup created${NC}"
fi

# Create backup manifest
cat > "backup_manifest_${TIMESTAMP}.json" <<EOF
{
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "backups": [
        {
            "type": "database",
            "file": "db_backup_${TIMESTAMP}.sql.gz",
            "size": $(stat -f%z "db_backup_${TIMESTAMP}.sql.gz" 2>/dev/null || stat -c%s "db_backup_${TIMESTAMP}.sql.gz" 2>/dev/null || echo 0)
        },
        {
            "type": "media",
            "file": "media_backup_${TIMESTAMP}.tar.gz",
            "size": $(stat -f%z "media_backup_${TIMESTAMP}.tar.gz" 2>/dev/null || stat -c%s "media_backup_${TIMESTAMP}.tar.gz" 2>/dev/null || echo 0)
        }
    ]
}
EOF

# Upload to S3
echo -e "${YELLOW}Uploading backups to S3...${NC}"
aws s3 sync . "s3://$S3_BUCKET/$S3_PREFIX/$TIMESTAMP/" \
    --region "$AWS_DEFAULT_REGION" \
    --exclude "*" \
    --include "*.gz" \
    --include "*.tar.gz" \
    --include "*.json" \
    --include "*.txt"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backups uploaded to S3${NC}"
else
    echo -e "${RED}✗ S3 upload failed${NC}"
    exit 1
fi

# Clean up old local backups
echo -e "${YELLOW}Cleaning up local backup files...${NC}"
rm -f "$BACKUP_DIR"/*.gz "$BACKUP_DIR"/*.json "$BACKUP_DIR"/*.txt

# Clean up old S3 backups (older than retention period)
echo -e "${YELLOW}Cleaning up old S3 backups (older than $RETENTION_DAYS days)...${NC}"
CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y%m%d 2>/dev/null || echo "")

if [ ! -z "$CUTOFF_DATE" ]; then
    aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" | while read -r line; do
        BACKUP_DATE=$(echo $line | awk '{print $2}' | cut -d'_' -f1)
        if [ ! -z "$BACKUP_DATE" ] && [ "$BACKUP_DATE" -lt "$CUTOFF_DATE" ]; then
            BACKUP_FOLDER=$(echo $line | awk '{print $2}')
            echo "Deleting old backup: $BACKUP_FOLDER"
            aws s3 rm "s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_FOLDER" --recursive
        fi
    done
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Backup completed successfully!"
echo "==========================================${NC}"
echo "Backup location: s3://$S3_BUCKET/$S3_PREFIX/$TIMESTAMP/"
echo ""







