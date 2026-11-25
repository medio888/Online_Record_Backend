#!/usr/bin/env bash
set -o errexit

python manage.py migrate --no-input

# Админ создаётся один раз, если заданы DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --no-input || true
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2
