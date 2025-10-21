#!/bin/bash
# Railway entrypoint script
# This script runs before starting the web server

set -e

echo "🚀 Starting Railway deployment..."

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

echo "✅ Deployment preparation complete!"

# Start the application (this will be replaced by Railway's start command)
exec "$@"
