#!/usr/bin/env bash
# Exit on error
set -o errexit

# Run migrations
python manage.py migrate

# Create initial superuser
python manage.py init_admin

# Start Gunicorn
exec gunicorn ctr_project.wsgi:application
