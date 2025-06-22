# Django REST Framework Project with uv, PostgreSQL, and Docker

A modern Django REST Framework project template using uv for dependency management, PostgreSQL as the database, and Docker for containerization.

## Features

- 🚀 **Django 4.2** with Django REST Framework
- 📦 **uv** for fast Python package management
- 🐘 **PostgreSQL** database with pgAdmin support
- 🐳 **Docker** and Docker Compose for development and production
- 🎨 **Ruff** for code linting and formatting
- 📁 **Modular app structure** with core and accounts apps
- 🔐 **Token-based authentication** with user management
- 🏗️ **Hierarchical models** with soft delete functionality
- 📊 **Admin interface** with enhanced user management
- 🧪 **Testing setup** with pytest-django
- 🔧 **Multiple environment configurations** (development, production, test)
- ⚙️ **python-decouple** for environment variable management
- 🕐 **Timezone-aware datetimes** with UTC default

## Project Structure

```
uv-django-test/
├── apps/
│   ├── accounts/          # User management and authentication
│   └── core/              # Core functionality (tags, categories)
├── config/
│   ├── settings/
│   │   ├── base.py        # Base settings
│   │   ├── development.py # Development settings
│   │   ├── production.py  # Production settings
│   │   └── test.py        # Test settings
│   ├── urls.py            # Main URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── docker/                # Docker configuration files
├── static/                # Static files
├── media/                 # Media files
├── templates/             # Django templates
├── logs/                  # Application logs
├── docker-compose.yml     # Development Docker Compose
├── docker-compose.prod.yml # Production Docker Compose
├── Dockerfile             # Production Dockerfile
├── Dockerfile.dev         # Development Dockerfile
├── pyproject.toml         # Python project configuration
├── .env.example           # Environment variables template
└── manage.py              # Django management script
```

## Quick Start

### Prerequisites

- Python 3.12+
- uv (install from https://github.com/astral-sh/uv)
- Docker and Docker Compose
- PostgreSQL (for local development without Docker)

### Key Features

- **Environment Management**: Uses `python-decouple` for clean environment variable handling
- **Timezone Aware**: All datetimes are timezone-aware and stored in UTC
- **Connection Pooling**: PostgreSQL connection pooling enabled for better performance
- **Modern Django**: Uses Django 5.1 with latest features

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd uv-django-test
   ```

2. **Install dependencies with uv:**
   ```bash
   uv sync
   ```

3. **Create environment file:**

   **For Docker development:**
   ```bash
   cp .env.example .env
   # Uses 'db' as database host (Docker service name)
   ```

   **For local development:**
   ```bash
   cp .env.local.example .env
   # Uses 'localhost' as database host
   ```

4. **Run with Docker Compose (Recommended):**
   ```bash
   docker-compose up --build
   ```

5. **Or run locally (requires local PostgreSQL):**
   ```bash
   # Start PostgreSQL service locally
   # Create database and user as specified in .env

   # Run migrations
   uv run python manage.py migrate

   # Create superuser
   uv run python manage.py createsuperuser

   # Start development server
   uv run python manage.py runserver
   ```

## Development

### Using Docker (Recommended)

The project includes separate Docker configurations for development and production:

- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `Dockerfile.dev` - Development container
- `Dockerfile` - Production container

**Start development environment:**
```bash
docker-compose up --build
```

**View logs:**
```bash
docker-compose logs -f web
```

**Run Django commands:**
```bash
docker-compose exec web uv run python manage.py migrate
docker-compose exec web uv run python manage.py createsuperuser
docker-compose exec web uv run python manage.py collectstatic
```

### Local Development

**Install development dependencies:**
```bash
uv sync --extra dev
```

**Database setup:**
```bash
# Create PostgreSQL database
createdb django_db

# Run migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser
```

**Code formatting and linting:**
```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

**Run tests:**
```bash
uv run pytest
```

## API Endpoints

### Authentication
- `POST /api/accounts/login/` - Login and get token
- `POST /api/accounts/logout/` - Logout (delete token)
- `GET /api/accounts/users/me/` - Get current user profile
- `PUT /api/accounts/users/me/` - Update current user profile
- `POST /api/accounts/users/change_password/` - Change password

### Users
- `GET /api/accounts/users/` - List public users
- `POST /api/accounts/users/` - Register new user
- `GET /api/accounts/users/{id}/` - Get user details
- `GET /api/accounts/users/{id}/profile/` - Get user public profile

### Core
- `GET /api/core/tags/` - List tags
- `POST /api/core/tags/` - Create tag
- `GET /api/core/categories/` - List categories
- `POST /api/core/categories/` - Create category
- `GET /api/core/categories/root_categories/` - Get root categories

### Admin
- `GET /admin/` - Django admin interface

## Django Settings Configuration

The project uses different Django settings modules for different environments:

### Settings Modules

- **`config.settings.base`** - Common settings shared across all environments
- **`config.settings.development`** - Development-specific settings
- **`config.settings.production`** - Production-specific settings  
- **`config.settings.test`** - Test-specific settings

### Settings Module Selection

**Automatic Selection:**
- **Local Development**: `manage.py` defaults to `config.settings.development`
- **Production WSGI**: `wsgi.py` defaults to `config.settings.production`
- **Testing**: `pytest` uses `config.settings.test`

**Manual Override:**
```bash
# Override settings module
export DJANGO_SETTINGS_MODULE=config.settings.production
uv run python manage.py runserver

# Or set in environment
DJANGO_SETTINGS_MODULE=config.settings.development uv run python manage.py migrate
```

**Docker Configuration:**
- **Development**: `docker-compose.yml` sets `DJANGO_SETTINGS_MODULE=config.settings.development`
- **Production**: `docker-compose.prod.yml` sets `DJANGO_SETTINGS_MODULE=config.settings.production`

## Environment Variables

Copy the appropriate `.env` file for your environment:

**For Docker Development:**
```bash
cp .env.example .env
```

**For Local Development:**
```bash
cp .env.local.example .env
```

### Docker Development (.env.example)

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.development

# Database Configuration (Docker)
DATABASE_URL=postgresql://django_user:django_password@db:5432/django_db
DB_HOST=db
DB_NAME=django_db
DB_USER=django_user
DB_PASSWORD=django_password
DB_PORT=5432

# Cache Configuration
REDIS_URL=redis://redis:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Local Development (.env.local.example)

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.development

# Database Configuration (Local)
DATABASE_URL=postgresql://django_user:django_password@localhost:5432/django_db
DB_HOST=localhost
DB_NAME=django_db
DB_USER=django_user
DB_PASSWORD=django_password
DB_PORT=5432

# Cache Configuration (Optional)
# REDIS_URL=redis://localhost:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Production Environment

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key
DJANGO_SETTINGS_MODULE=config.settings.production

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security Settings
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000

# External Services
REDIS_URL=redis://redis-host:6379/0
EMAIL_HOST=smtp.youremail.com
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password
```

<old_text>
## Troubleshooting

### Common Issues

**Database connection errors:**
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists

**Docker build failures:**
- Clear Docker cache: `docker system prune -a`
- Rebuild without cache: `docker-compose build --no-cache`

**Permission errors:**
- Ensure proper file permissions
- Check Docker daemon is running

**Import errors:**
- Ensure uv environment is activated
- Check PYTHONPATH includes project root
- Verify all dependencies are installed

## Production Deployment

### Docker Production Setup

The project includes optimized multi-stage Docker builds for minimal production image sizes:

- **`Dockerfile`** - Standard multi-stage build (~200MB)
- **`Dockerfile.alpine`** - Ultra-minimal Alpine-based build (~80MB)

#### Option 1: Standard Production Build

1. **Create production environment file:**
   ```bash
   cp .env.example .env.prod
   # Configure production settings
   ```

2. **Build and run production containers:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Run production migrations:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
   docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
   ```

#### Option 2: Ultra-Minimal Alpine Build

For the smallest possible image size:

```bash
# Build with Alpine (smallest image)
docker-compose -f docker-compose.alpine.yml up --build -d

# Run migrations
docker-compose -f docker-compose.alpine.yml exec web python manage.py migrate
docker-compose -f docker-compose.alpine.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.alpine.yml exec web python manage.py createsuperuser
```

#### Multi-Stage Build Benefits

- **Smaller Images**: Production images are 60-80% smaller than single-stage builds
- **Security**: Minimal attack surface with only runtime dependencies
- **Performance**: Faster deployment and container startup times
- **Efficiency**: Separate build and runtime environments

### Production Settings

The production configuration includes:
- SSL/HTTPS enforcement
- Static file serving with WhiteNoise
- Redis caching
- Optimized logging
- Security headers
- Rate limiting

## Testing

Run tests with pytest:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=apps

# Run specific test file
uv run pytest apps/accounts/tests.py

# Run tests in verbose mode
uv run pytest -v
```

## Code Quality

This project uses Ruff for linting and formatting:

```bash
# Check code
uv run ruff check .

# Format code
uv run ruff format .

# Fix issues automatically
uv run ruff check --fix .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

**Database connection errors:**
- Ensure PostgreSQL is running
- Check database credentials in `.env`
- Verify database exists
- For Docker: ensure using `DB_HOST=db`
- For local: ensure using `DB_HOST=localhost`

**Settings module errors:**
- Verify `DJANGO_SETTINGS_MODULE` is set correctly
- Check if settings file exists and has no syntax errors
- For Docker: settings are set in docker-compose files
- For local: check your `.env` file or export manually

**Docker build failures:**
- Clear Docker cache: `docker system prune -a`
- Rebuild without cache: `docker-compose build --no-cache`

**Permission errors:**
- Ensure proper file permissions
- Check Docker daemon is running

**Import errors:**
- Ensure uv environment is activated
- Check PYTHONPATH includes project root
- Verify all dependencies are installed

### Settings Debugging

Check which settings module is being used:
```bash
# In Django shell
uv run python manage.py shell
>>> from django.conf import settings
>>> settings.SETTINGS_MODULE
'config.settings.development'

# Check specific setting values
>>> settings.DEBUG
True
>>> settings.DATABASES['default']['HOST']
'db'
```

### Logs

Check application logs:
```bash
# Docker logs
docker-compose logs -f web

# Local logs
tail -f logs/django.log

# Check Django settings in logs
docker-compose exec web uv run python manage.py diffsettings
```

## Support

For issues and questions, please open an issue in the repository.
