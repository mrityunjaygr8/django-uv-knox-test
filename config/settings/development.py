"""
Development settings for Django project.
"""

from .base import *
from decouple import config
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Database
# Use DATABASE_URL if available, otherwise individual settings
DATABASE_URL = config("DATABASE_URL", default=None)
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL)
    }
    # Add connection pooling for PostgreSQL
    if "postgresql" in DATABASE_URL:
        DATABASES["default"]["OPTIONS"] = {
            "pool": {
                "min_size": 2,
                "max_size": 10,
                "timeout": 30,
            }
        }
else:
    # Fallback to individual database settings
    # In Docker: DB_HOST=db, locally: DB_HOST=localhost
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="django_db"),
            "USER": config("DB_USER", default="django_user"),
            "PASSWORD": config("DB_PASSWORD", default="django_password"),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
            "OPTIONS": {
                "pool": {
                    "min_size": 2,
                    "max_size": 10,
                    "timeout": 30,
                },
            },
        }
    }

# Django REST Framework - Development settings
REST_FRAMEWORK.update({
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",  # Enable browsable API in dev
    ],
})

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Static files - serve from Django in development
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Disable security features in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging configuration for development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Development tools
if DEBUG:
    # Add any development-specific apps here
    INSTALLED_APPS += [
        # "debug_toolbar",  # Uncomment if you want to use Django Debug Toolbar
    ]

    # Add debug toolbar middleware if enabled
    # MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

    # Debug toolbar settings
    # INTERNAL_IPS = ["127.0.0.1", "localhost"]
