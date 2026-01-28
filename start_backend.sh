#!/bin/bash
# Startup script for ProvenPick Staging Backend

cd /home/sai/Desktop/Projects_and_Folders/my_code/provenpick

# Set environment variables
export PYTHONPATH=/home/sai/Desktop/Projects_and_Folders/my_code/provenpick-staging:$PYTHONPATH
export DB_NAME=provenpick
export DB_USER=provenpick
export DB_PASSWORD=provenpick
export DB_HOST=localhost
export DB_PORT=5432
export STAGING_ADMIN_TOKEN=provenpick-staging-secret-token-2026

# Start backend
echo "Starting ProvenPick Staging Backend..."
.venv/bin/python /home/sai/Desktop/Projects_and_Folders/my_code/provenpick-staging/backend/main.py
