# Dependencies stage - install Python dependencies only
FROM python:3.12-slim as dependencies

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for building Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official Docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set work directory
WORKDIR /app

# Copy only dependency files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies (including production extras)
# Use --compile-bytecode for faster startup
RUN uv sync --frozen --no-cache --extra prod --compile-bytecode

# Build stage - prepare application
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Copy virtual environment from dependencies stage
COPY --from=dependencies /app/.venv /app/.venv

# Copy uv from dependencies stage
COPY --from=dependencies /bin/uv /bin/uv

# Copy source code
COPY . .

# Collect static files using the virtual environment
RUN uv run python manage.py collectstatic --noinput

# Remove unnecessary files to reduce final image size
RUN find . -name "*.pyc" -delete \
    && find . -name "__pycache__" -type d -exec rm -rf {} + \
    && find . -name "*.po" -delete \
    && find . -name "*.pot" -delete \
    && rm -rf .git \
    && rm -rf tests \
    && rm -rf docs \
    && rm -rf .pytest_cache \
    && rm -rf .ruff_cache

# Production stage - minimal runtime image
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Install only essential runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Create non-root user with specific UID for consistency
RUN adduser --disabled-password --gecos '' --uid 1000 appuser

# Set work directory
WORKDIR /app

# Copy uv binary from builder stage
COPY --from=builder /bin/uv /bin/uv

# Copy the virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code and static files from builder stage
COPY --from=builder --chown=appuser:appuser /app /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/media /app/staticfiles \
    && chown -R appuser:appuser /app/logs /app/media /app/staticfiles

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check with simpler approach
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8000), timeout=5)" || exit 1

# Run gunicorn with optimized settings
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "sync", "--timeout", "60", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "100", "config.wsgi:application"]
