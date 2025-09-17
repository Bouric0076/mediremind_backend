#!/bin/bash

# Build script for Render deployment (Free Tier Optimized)
# This script is executed during the build phase on Render
# Optimized for 20-minute build time limit

set -e  # Exit on any error

echo "🚀 Starting build process for Render Free Tier..."
echo "⏰ Build started at: $(date)"

# Install Python dependencies with optimizations
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --verbosity=1

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --verbosity=1

# Create cache table if using database cache
echo "🔄 Setting up cache table..."
python manage.py createcachetable || echo "Cache table already exists or not needed"

echo "✅ Build process completed successfully!"
echo "⏰ Build finished at: $(date)"
echo "🎉 Ready for deployment on Render Free Tier!"

# Create superuser if it doesn't exist (optional)
# python manage.py shell -c "
# from django.contrib.auth import get_user_model;
# User = get_user_model();
# if not User.objects.filter(username='admin').exists():
#     User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
# "