#!/bin/bash
# Initialize database script

set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Running migrations..."
docker-compose exec web python manage.py migrate

echo "Creating superuser..."
docker-compose exec web python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

echo "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

echo "Database initialization complete!"







