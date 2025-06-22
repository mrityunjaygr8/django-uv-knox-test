"""
Test settings for Django project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in testing
ALLOWED_HOSTS = ["*"]

# Database - use in-memory SQLite for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Password hashers - use fast hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Cache - use dummy cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Static files - disable collectstatic in tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Media files - use temporary directory
MEDIA_ROOT = "/tmp/test_media"

# Django REST Framework - Test settings
REST_FRAMEWORK.update({
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "knox.auth.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
})

# Django REST Knox Settings for Testing
REST_KNOX = {
    "SECURE_HASH_ALGORITHM": "cryptography.hazmat.primitives.hashes.SHA512",
    "AUTH_TOKEN_CHARACTER_LENGTH": 64,
    "TOKEN_TTL": None,  # No expiration for tests
    "USER_SERIALIZER": "apps.accounts.serializers.UserSerializer",
    "TOKEN_LIMIT_PER_USER": None,  # No limit for tests
    "AUTO_REFRESH": False,  # Disable for faster tests
}

# CORS settings for testing
CORS_ALLOW_ALL_ORIGINS = True

# Disable security features in testing
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging configuration for testing - minimal logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "propagate": False,
        },
        "django.request": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}

# Celery settings for testing (if using Celery)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Test runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"
