FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy entrypoint script (if exists, otherwise create inline)
RUN echo '#!/bin/bash\nset -e\necho "Waiting for database..."\nwhile ! nc -z db 5432; do sleep 0.1; done\necho "Database ready!"\nwhile ! nc -z redis 6379; do sleep 0.1; done\necho "Redis ready!"\npython manage.py migrate --noinput || true\npython manage.py collectstatic --noinput || true\nexec "$@"' > /usr/local/bin/docker-entrypoint.sh && chmod +x /usr/local/bin/docker-entrypoint.sh

# Create media and logs directories
RUN mkdir -p /app/media /app/logs

# Expose ports
EXPOSE 8001

# Use entrypoint script
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "iot_platform.asgi:application"]

