#!/bin/bash
# Restore Backup from S3
# Usage: ./restore-from-s3.sh <backup_timestamp>
# Example: ./restore-from-s3.sh 20240101_020000

set -e

BACKUP_TIMESTAMP=${1}
S3_BUCKET=${S3_BUCKET:-"smartmailbox-backups"}
S3_PREFIX=${S3_PREFIX:-"backups"}

if [ -z "$BACKUP_TIMESTAMP" ]; then
    echo "ERROR: Please provide backup timestamp"
    echo "Usage: ./restore-from-s3.sh <backup_timestamp>"
    echo ""
    echo "Available backups:"
    aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/" | awk '{print $2}'
    exit 1
fi

echo "=========================================="
echo "Restoring from S3 Backup"
echo "=========================================="
echo "Backup: $BACKUP_TIMESTAMP"
echo ""

# Download backup
TEMP_DIR="/tmp/restore_${BACKUP_TIMESTAMP}"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "Downloading backup from S3..."
aws s3 sync "s3://$S3_BUCKET/$S3_PREFIX/$BACKUP_TIMESTAMP/" .

# Restore database
if [ -f "db_backup_${BACKUP_TIMESTAMP}.sql.gz" ]; then
    echo "Restoring database..."
    gunzip -c "db_backup_${BACKUP_TIMESTAMP}.sql.gz" | \
        docker-compose -f docker-compose.prod.yml exec -T db psql -U smartmailbox_user smartmailbox
    echo "✓ Database restored"
fi

# Restore media files
if [ -f "media_backup_${BACKUP_TIMESTAMP}.tar.gz" ]; then
    echo "Restoring media files..."
    docker-compose -f docker-compose.prod.yml exec -T web sh -c "cd /app && tar xzf -" < "media_backup_${BACKUP_TIMESTAMP}.tar.gz"
    echo "✓ Media files restored"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Restore completed!"
echo "You may need to restart the web container:"
echo "docker-compose -f docker-compose.prod.yml restart web"







