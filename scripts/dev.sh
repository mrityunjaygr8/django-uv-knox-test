#!/usr/bin/env bash

# Development helper script for fast Docker operations
# Usage: ./scripts/dev.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.fast.yml"
CACHE_IMAGE="uv-django-test:dev-cache"

# Helper functions
log() {
    echo -e "${GREEN}[DEV]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
    fi
}

# Build only if needed (check for changes)
smart_build() {
    local force_build=false

    if [[ "$1" == "--force" ]]; then
        force_build=true
        shift
    fi

    # Check if image exists
    if ! docker image inspect $CACHE_IMAGE > /dev/null 2>&1 || $force_build; then
        log "Building development image..."
        docker compose -f $COMPOSE_FILE build --parallel
        log "Build complete!"
    else
        # Check if Dockerfile or requirements have changed
        local dockerfile_changed=$(find . -name "Dockerfile*" -newer <(docker image inspect $CACHE_IMAGE --format '{{.Created}}' 2>/dev/null || echo "1970-01-01") | wc -l)
        local deps_changed=$(find . -name "pyproject.toml" -o -name "uv.lock" -newer <(docker image inspect $CACHE_IMAGE --format '{{.Created}}' 2>/dev/null || echo "1970-01-01") | wc -l)

        if [[ $dockerfile_changed -gt 0 ]] || [[ $deps_changed -gt 0 ]]; then
            log "Detected changes in Dockerfile or dependencies. Rebuilding..."
            docker compose -f $COMPOSE_FILE build --parallel
        else
            info "Using cached image (use --force to rebuild)"
        fi
    fi
}

# Quick start for development
quick_start() {
    log "Starting development environment..."
    smart_build
    docker compose -f $COMPOSE_FILE up -d db redis

    # Wait for database to be ready
    log "Waiting for database..."
    until docker compose -f $COMPOSE_FILE exec -T db pg_isready -U django_user -d django_db > /dev/null 2>&1; do
        sleep 1
    done

    # Start web service
    docker compose -f $COMPOSE_FILE up -d web

    log "Development environment is ready!"
    info "Web server: http://localhost:8000"
    info "Database: localhost:5432"
    info "Redis: localhost:6379"
}

# Fast restart of just the web service
fast_restart() {
    log "Fast restarting web service..."
    docker compose -f $COMPOSE_FILE restart web
    log "Web service restarted!"
}

# Show logs with follow
show_logs() {
    local service=${1:-web}
    docker compose -f $COMPOSE_FILE logs -f $service
}

# Execute Django management commands
django_cmd() {
    if [[ $# -eq 0 ]]; then
        error "Please provide a Django management command"
    fi

    docker compose -f $COMPOSE_FILE exec web uv run python manage.py "$@"
}

# Open shell in container
shell() {
    local shell_type=${1:-bash}
    case $shell_type in
        bash|sh)
            docker compose -f $COMPOSE_FILE exec web $shell_type
            ;;
        django|python)
            docker compose -f $COMPOSE_FILE exec web uv run python manage.py shell
            ;;
        *)
            error "Unknown shell type: $shell_type. Use: bash, sh, django, or python"
            ;;
    esac
}

# Clean up everything
cleanup() {
    log "Cleaning up development environment..."
    docker compose -f $COMPOSE_FILE down -v --remove-orphans
    docker system prune -f
    log "Cleanup complete!"
}

# Run tests
run_tests() {
    log "Running tests..."
    docker compose -f $COMPOSE_FILE exec web uv run pytest "$@"
}

# Database operations
db_operations() {
    case $1 in
        migrate)
            django_cmd migrate
            ;;
        makemigrations)
            django_cmd makemigrations "${@:2}"
            ;;
        reset)
            warn "This will delete all data in the database!"
            read -p "Are you sure? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker compose -f $COMPOSE_FILE exec db psql -U django_user -d django_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
                django_cmd migrate
                log "Database reset complete!"
            fi
            ;;
        backup)
            local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
            docker compose -f $COMPOSE_FILE exec -T db pg_dump -U django_user django_db > $backup_file
            log "Database backed up to: $backup_file"
            ;;
        restore)
            if [[ -z "$2" ]]; then
                error "Please provide backup file path"
            fi
            docker compose -f $COMPOSE_FILE exec -T db psql -U django_user django_db < "$2"
            log "Database restored from: $2"
            ;;
        *)
            error "Unknown database operation: $1. Use: migrate, makemigrations, reset, backup, restore"
            ;;
    esac
}

# Watch for file changes and restart
watch() {
    log "Starting file watcher..."
    docker compose -f $COMPOSE_FILE --profile watcher up file-watcher
}

# Show help
show_help() {
    echo "Django Development Helper Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start         Quick start development environment"
    echo "  stop          Stop all services"
    echo "  restart       Fast restart web service"
    echo "  build         Build development images"
    echo "  build --force Force rebuild images"
    echo "  logs [service] Show logs (default: web)"
    echo "  shell [type]  Open shell (bash, django)"
    echo "  test [args]   Run tests"
    echo "  watch         Start file watcher for auto-reload"
    echo "  cleanup       Clean up everything"
    echo ""
    echo "Django commands:"
    echo "  manage [cmd]  Run Django management command"
    echo "  migrate       Run database migrations"
    echo "  makemigrations Create new migrations"
    echo ""
    echo "Database operations:"
    echo "  db migrate           Run migrations"
    echo "  db makemigrations    Create migrations"
    echo "  db reset            Reset database (WARNING: deletes data)"
    echo "  db backup           Backup database"
    echo "  db restore [file]   Restore from backup"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start development environment"
    echo "  $0 manage createsuperuser   # Create Django superuser"
    echo "  $0 shell django             # Open Django shell"
    echo "  $0 test --cov               # Run tests with coverage"
    echo "  $0 logs web                 # Follow web service logs"
}

# Main script logic
main() {
    check_docker

    case ${1:-help} in
        start)
            quick_start
            ;;
        stop)
            log "Stopping development environment..."
            docker compose -f $COMPOSE_FILE down
            ;;
        restart)
            fast_restart
            ;;
        build)
            smart_build "$@"
            ;;
        logs)
            show_logs "${@:2}"
            ;;
        shell)
            shell "${@:2}"
            ;;
        test)
            run_tests "${@:2}"
            ;;
        manage)
            django_cmd "${@:2}"
            ;;
        migrate)
            db_operations migrate
            ;;
        makemigrations)
            db_operations makemigrations "${@:2}"
            ;;
        db)
            db_operations "${@:2}"
            ;;
        watch)
            watch
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown command: $1. Use '$0 help' for available commands."
            ;;
    esac
}

# Run main function with all arguments
main "$@"
