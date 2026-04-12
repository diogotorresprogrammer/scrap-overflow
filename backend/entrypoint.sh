#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting gunicorn..."
exec gunicorn -b 0.0.0.0:8000 main:app
