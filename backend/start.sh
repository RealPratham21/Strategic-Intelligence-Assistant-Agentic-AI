#!/bin/bash
# Startup script for Render deployment

# Get port from environment variable (Render provides this)
PORT=${PORT:-8000}

# Change to backend directory if not already there
cd "$(dirname "$0")" || exit

# Start the application
echo "Starting Strategic Intelligence Assistant API..."
echo "Port: $PORT"
echo "Host: 0.0.0.0"
exec uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
