from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import os
import sys
import platform
import socket
import subprocess


class Command(BaseCommand):
    help = 'Display debug information for troubleshooting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information',
        )
        parser.add_argument(
            '--check-services',
            action='store_true',
            help='Check external service connectivity',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Django Debug Information'))
        self.stdout.write('=' * 60)

        self._show_environment_info()
        self._show_django_info()
        self._show_database_info()
        self._show_cache_info()

        if options['check_services']:
            self._check_external_services()

        if options['verbose']:
            self._show_detailed_settings()

    def _show_environment_info(self):
        self.stdout.write(self.style.WARNING('\n📋 Environment Information:'))
        self.stdout.write(f"Python Version: {sys.version}")
        self.stdout.write(f"Platform: {platform.platform()}")
        self.stdout.write(f"Working Directory: {os.getcwd()}")
        self.stdout.write(f"Python Path: {sys.path[0]}")

        # Environment variables
        important_vars = [
            'DJANGO_SETTINGS_MODULE', 'DEBUG', 'DATABASE_URL',
            'REDIS_URL', 'SECRET_KEY', 'ALLOWED_HOSTS'
        ]

        self.stdout.write("\n🔑 Environment Variables:")
        for var in important_vars:
            value = os.environ.get(var, 'Not set')
            if 'SECRET' in var or 'PASSWORD' in var:
                value = '***HIDDEN***' if value != 'Not set' else 'Not set'
            self.stdout.write(f"  {var}: {value}")

    def _show_django_info(self):
        self.stdout.write(self.style.WARNING('\n⚙️ Django Configuration:'))
        self.stdout.write(f"Settings Module: {settings.SETTINGS_MODULE}")
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"SECRET_KEY: {'SET' if settings.SECRET_KEY else 'NOT SET'}")
        self.stdout.write(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        self.stdout.write(f"TIME_ZONE: {settings.TIME_ZONE}")
        self.stdout.write(f"USE_TZ: {settings.USE_TZ}")

        # Installed apps
        self.stdout.write(f"\n📦 Local Apps:")
        local_apps = [app for app in settings.INSTALLED_APPS if app.startswith('apps.')]
        for app in local_apps:
            self.stdout.write(f"  ✓ {app}")

    def _show_database_info(self):
        self.stdout.write(self.style.WARNING('\n🗄️ Database Information:'))

        db_config = settings.DATABASES['default']
        self.stdout.write(f"Engine: {db_config['ENGINE']}")
        self.stdout.write(f"Name: {db_config['NAME']}")
        self.stdout.write(f"Host: {db_config['HOST']}")
        self.stdout.write(f"Port: {db_config['PORT']}")
        self.stdout.write(f"User: {db_config['USER']}")

        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"✓ Database Connection: OK"))
                self.stdout.write(f"  Version: {version}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Database Connection: FAILED"))
            self.stdout.write(f"  Error: {str(e)}")

    def _show_cache_info(self):
        self.stdout.write(self.style.WARNING('\n💾 Cache Information:'))

        cache_config = settings.CACHES['default']
        self.stdout.write(f"Backend: {cache_config['BACKEND']}")

        if 'LOCATION' in cache_config:
            self.stdout.write(f"Location: {cache_config['LOCATION']}")

        # Test cache connection
        try:
            cache.set('debug_test', 'test_value', 10)
            value = cache.get('debug_test')
            if value == 'test_value':
                self.stdout.write(self.style.SUCCESS(f"✓ Cache Connection: OK"))
                cache.delete('debug_test')
            else:
                self.stdout.write(self.style.ERROR(f"✗ Cache Connection: FAILED (Read/Write issue)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Cache Connection: FAILED"))
            self.stdout.write(f"  Error: {str(e)}")

    def _check_external_services(self):
        self.stdout.write(self.style.WARNING('\n🌐 External Service Connectivity:'))

        services = [
            ('Database', settings.DATABASES['default']['HOST'], int(settings.DATABASES['default']['PORT'])),
        ]

        # Add Redis if configured
        if hasattr(settings, 'CACHES') and 'redis' in settings.CACHES['default']['BACKEND'].lower():
            redis_url = settings.CACHES['default'].get('LOCATION', '')
            if redis_url and redis_url.startswith('redis://'):
                # Parse redis://host:port/db
                parts = redis_url.replace('redis://', '').split(':')
                if len(parts) >= 2:
                    host = parts[0]
                    port = int(parts[1].split('/')[0])
                    services.append(('Redis', host, port))

        for service_name, host, port in services:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    self.stdout.write(self.style.SUCCESS(f"✓ {service_name} ({host}:{port}): REACHABLE"))
                else:
                    self.stdout.write(self.style.ERROR(f"✗ {service_name} ({host}:{port}): UNREACHABLE"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ {service_name} ({host}:{port}): ERROR - {str(e)}"))

    def _show_detailed_settings(self):
        self.stdout.write(self.style.WARNING('\n🔧 Detailed Settings:'))

        # Static files
        self.stdout.write(f"\n📁 Static Files:")
        self.stdout.write(f"  STATIC_URL: {settings.STATIC_URL}")
        self.stdout.write(f"  STATIC_ROOT: {settings.STATIC_ROOT}")
        self.stdout.write(f"  STATICFILES_DIRS: {settings.STATICFILES_DIRS}")

        # Media files
        self.stdout.write(f"\n🖼️ Media Files:")
        self.stdout.write(f"  MEDIA_URL: {settings.MEDIA_URL}")
        self.stdout.write(f"  MEDIA_ROOT: {settings.MEDIA_ROOT}")

        # Security settings
        self.stdout.write(f"\n🔒 Security Settings:")
        security_settings = [
            'SECURE_SSL_REDIRECT', 'SECURE_HSTS_SECONDS',
            'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE'
        ]
        for setting in security_settings:
            value = getattr(settings, setting, 'Not set')
            self.stdout.write(f"  {setting}: {value}")

        # CORS settings
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            self.stdout.write(f"\n🌐 CORS Settings:")
            self.stdout.write(f"  CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
            self.stdout.write(f"  CORS_ALLOW_CREDENTIALS: {getattr(settings, 'CORS_ALLOW_CREDENTIALS', 'Not set')}")

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Debug information complete! 🎉'))
