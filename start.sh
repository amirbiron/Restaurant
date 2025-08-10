#!/bin/bash

# Startup script for Render deployment
# Ensures only one bot instance is running

echo "Starting Telegram Bot Service..."
echo "Port: $PORT"
echo "Workers: 1 (singleton mode)"

# Kill any existing Python processes that might be running the bot
# This helps prevent conflict errors
echo "Cleaning up any existing bot processes..."
pkill -f "telegram" || true
pkill -f "flask_bot" || true
sleep 2

# Export environment to ensure BOT_TOKEN is available
export BOT_TOKEN="${BOT_TOKEN}"

# Start gunicorn with single worker to prevent multiple bot instances
echo "Starting Gunicorn with Flask app..."
exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers 1 \
    --threads 1 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --worker-class sync \
    app:application