#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade
echo "Migrations completed successfully."

exec python app.py
