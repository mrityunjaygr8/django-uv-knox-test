.PHONY: help install dev-install format lint test clean migrate superuser shell runserver docker-build docker-up docker-down docker-logs production-build production-up production-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install production dependencies"
	@echo "  dev-install      Install development dependencies"
	@echo "  format          Format code with ruff"
	@echo "  lint            Lint code with ruff"
	@echo "  test            Run tests with pytest"
	@echo "  clean           Clean cache and temporary files"
	@echo "  migrate         Run database migrations"
	@echo "  superuser       Create Django superuser"
	@echo "  shell           Open Django shell"
	@echo "  runserver       Start development server"
	@echo ""
	@echo "Fast Development Commands:"
	@echo "  dev-start       Quick start development environment"
	@echo "  dev-stop        Stop development environment"
	@echo "  dev-restart     Fast restart web service only"
	@echo "  dev-logs        Show development logs"
	@echo "  dev-shell       Open development shell"
	@echo "  dev-test        Run tests in development environment"
	@echo "  dev-watch       Start file watcher for auto-reload"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build    Build Docker containers"
	@echo "  docker-up       Start Docker development environment"
	@echo "  docker-down     Stop Docker development environment"
	@echo "  docker-logs     Show Docker logs"
	@echo "  production-build Build production Docker containers"
	@echo "  production-up   Start production environment"
	@echo "  production-down Stop production environment"

# Python/uv commands
install:
	uv sync --frozen

dev-install:
	uv sync --frozen --extra dev

format:
	uv run ruff format .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

test:
	uv run pytest

test-cov:
	uv run pytest --cov=apps --cov-report=html

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

# Django commands
migrate:
	uv run python manage.py migrate

makemigrations:
	uv run python manage.py makemigrations

superuser:
	uv run python manage.py createsuperuser

shell:
	uv run python manage.py shell

runserver:
	uv run python manage.py runserver

collectstatic:
	uv run python manage.py collectstatic --noinput

# Docker development commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-restart:
	docker-compose restart

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec web bash

docker-django-shell:
	docker-compose exec web uv run python manage.py shell

docker-migrate:
	docker-compose exec web uv run python manage.py migrate

docker-makemigrations:
	docker-compose exec web uv run python manage.py makemigrations

docker-superuser:
	docker-compose exec web uv run python manage.py createsuperuser

docker-collectstatic:
	docker-compose exec web uv run python manage.py collectstatic --noinput

docker-test:
	docker-compose exec web uv run pytest

# Production Docker commands
production-build:
	docker-compose -f docker-compose.prod.yml build

production-up:
	docker-compose -f docker-compose.prod.yml up -d

production-down:
	docker-compose -f docker-compose.prod.yml down

production-logs:
	docker-compose -f docker-compose.prod.yml logs -f

production-migrate:
	docker-compose -f docker-compose.prod.yml exec web uv run python manage.py migrate

production-collectstatic:
	docker-compose -f docker-compose.prod.yml exec web uv run python manage.py collectstatic --noinput

production-superuser:
	docker-compose -f docker-compose.prod.yml exec web uv run python manage.py createsuperuser

# Development workflow
setup: dev-install migrate superuser
	@echo "Development environment setup complete!"

check: format lint test
	@echo "Code quality checks passed!"

docker-setup: docker-build docker-up docker-migrate docker-superuser
	@echo "Docker development environment setup complete!"

# Fast development setup
dev-setup: dev-start dev-migrate dev-superuser
	@echo "Fast development environment setup complete!"
	@echo "Access your app at: http://localhost:8000"

# Development workflow with fast commands
dev-check: dev-test format lint
	@echo "Development checks passed!"

# Fast Development Commands
dev-start:
	./scripts/dev.sh start

dev-stop:
	./scripts/dev.sh stop

dev-restart:
	./scripts/dev.sh restart

dev-logs:
	./scripts/dev.sh logs

dev-shell:
	./scripts/dev.sh shell

dev-django-shell:
	./scripts/dev.sh shell django

dev-test:
	./scripts/dev.sh test

dev-watch:
	./scripts/dev.sh watch

dev-build:
	./scripts/dev.sh build

dev-build-force:
	./scripts/dev.sh build --force

dev-migrate:
	./scripts/dev.sh migrate

dev-makemigrations:
	./scripts/dev.sh makemigrations

dev-superuser:
	./scripts/dev.sh manage createsuperuser

dev-cleanup:
	./scripts/dev.sh cleanup

# Database backup and restore (for development)
backup-db:
	docker-compose exec db pg_dump -U django_user django_db > backup.sql

restore-db:
	docker-compose exec -T db psql -U django_user django_db < backup.sql

dev-backup:
	./scripts/dev.sh db backup

dev-restore:
	./scripts/dev.sh db restore $(FILE)

# Reset development environment
reset: docker-down clean
	docker-compose up --build -d
	$(MAKE) docker-migrate
	@echo "Development environment reset complete!"

dev-reset:
	./scripts/dev.sh db reset
