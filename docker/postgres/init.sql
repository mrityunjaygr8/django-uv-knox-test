-- PostgreSQL initialization script for Django project

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE django_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'django_db')\gexec

-- Create user if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'django_user') THEN

      CREATE ROLE django_user LOGIN PASSWORD 'django_password';
   END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE django_db TO django_user;

-- Connect to the django_db database
\c django_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO django_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO django_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO django_user;

-- Set default privileges for future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO django_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO django_user;

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log completion
\echo 'PostgreSQL initialization completed successfully!'
