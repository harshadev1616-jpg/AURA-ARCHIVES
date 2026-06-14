#!/bin/bash
# Vercel build script for Django application

echo "Building Django application for Vercel..."

# Set Django settings module
export DJANGO_SETTINGS_MODULE=aura_archives.settings.production

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

# Collect static files (without input prompts)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Warning: Static file collection had issues"

# Create database cache table for Vercel deployment
echo "Creating cache table..."
python manage.py createcachetable 2>/dev/null || echo "Note: Cache table creation handled at runtime"

# Apply any pending database migrations
echo "Applying migrations..."
python manage.py migrate --noinput || echo "Note: migrations not applied during build"

# Ensure a superuser exists on the production database.
# Set ADMIN_EMAIL and ADMIN_PASSWORD in the Vercel project's Environment
# Variables; this creates/updates that superuser on every deploy. Skips if
# ADMIN_PASSWORD is unset.
echo "Ensuring admin user..."
python manage.py ensure_admin || echo "Note: ensure_admin skipped"

echo "Build completed successfully!"
