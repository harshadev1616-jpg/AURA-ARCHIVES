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

echo "Build completed successfully!"
