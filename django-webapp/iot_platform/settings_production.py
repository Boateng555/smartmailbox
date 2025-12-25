"""
Production settings for Hetzner cloud deployment.

This file extends the base settings.py and overrides values for production.
Use this by setting DJANGO_SETTINGS_MODULE=iot_platform.settings_production

All sensitive values should be set via environment variables.
"""

from .settings import *
from decouple import config, Csv
import dj_database_url
import os
from pathlib import Path

# ============================================================================
# SECURITY SETTINGS - CRITICAL FOR PRODUCTION
# ============================================================================

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set in production!")

# Allowed hosts - must be set to your domain(s)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS environment variable must be set in production!")

# API Domain for ESP32 devices
API_DOMAIN = config('API_DOMAIN', default='')
if not API_DOMAIN:
    print("WARNING: API_DOMAIN not set. ESP32 devices may not be able to connect.")

# Security settings for HTTPS
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Use PostgreSQL in production
DATABASE_URL = config('DATABASE_URL', default=None)
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set in production!")

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=config('DATABASE_SSL_REQUIRE', default=True, cast=bool),
    )
}

# ============================================================================
# STATIC FILES CONFIGURATION (for Nginx)
# ============================================================================

# Static files will be collected to STATIC_ROOT and served by Nginx
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Ensure staticfiles directory exists
STATIC_ROOT.mkdir(exist_ok=True)

# WhiteNoise for serving static files (fallback if Nginx not configured)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise middleware (after SecurityMiddleware, before other middleware)
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Media files (served by Nginx in production)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_ROOT.mkdir(exist_ok=True)

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

REDIS_HOST = config('REDIS_HOST', default='127.0.0.1')
REDIS_PORT = config('REDIS_PORT', default=6379, cast=int)
REDIS_PASSWORD = config('REDIS_PASSWORD', default=None)

# Build Redis URL for Channels
if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
            "password": REDIS_PASSWORD if REDIS_PASSWORD else None,
        },
    },
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django_errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'devices': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL_DEVICES', default='INFO'),
            'propagate': False,
        },
        'web': {
            'handlers': ['console', 'file'],
            'level': config('LOG_LEVEL_WEB', default='INFO'),
            'propagate': False,
        },
    },
}

# ============================================================================
# EMAIL CONFIGURATION (Optional)
# ============================================================================

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@' + (ALLOWED_HOSTS[0] if ALLOWED_HOSTS else 'localhost'))

# ============================================================================
# PUSH NOTIFICATIONS (VAPID Keys)
# ============================================================================

VAPID_PUBLIC_KEY = config('VAPID_PUBLIC_KEY', default='')
VAPID_PRIVATE_KEY = config('VAPID_PRIVATE_KEY', default='')
VAPID_ADMIN_EMAIL = config('VAPID_ADMIN_EMAIL', default='admin@' + (ALLOWED_HOSTS[0] if ALLOWED_HOSTS else 'localhost'))

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Cache configuration (Redis)
try:
    import django_redis
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PASSWORD': REDIS_PASSWORD if REDIS_PASSWORD else None,
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'IGNORE_EXCEPTIONS': True,
            }
        }
    }
except ImportError:
    # Fallback to basic Redis cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================

# Admin site header
ADMIN_SITE_HEADER = "Smart Camera IoT Platform - Admin"
ADMIN_SITE_TITLE = "Smart Camera Admin"
ADMIN_SITE_INDEX_TITLE = "Welcome to Smart Camera Administration"

# ============================================================================
# DEPLOYMENT NOTES
# ============================================================================

# To use this settings file:
# 1. Set environment variable: export DJANGO_SETTINGS_MODULE=iot_platform.settings_production
# 2. Or use --settings flag: python manage.py runserver --settings=iot_platform.settings_production
# 3. Ensure all required environment variables are set (see .env.example)
# 4. Run: python manage.py collectstatic
# 5. Configure Nginx to serve static files from STATIC_ROOT
# 6. Configure Nginx to serve media files from MEDIA_ROOT

