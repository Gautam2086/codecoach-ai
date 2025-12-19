#!/bin/bash
# Combined startup script for Railway deployment
# Runs both the token server and LiveKit agent in one container

set -e

echo "Starting CodeCoach backend..."

# Start token server in background
echo "Starting token server on port ${TOKEN_SERVER_PORT:-8080}..."
python token_server.py &
TOKEN_PID=$!

# Give token server a moment to start
sleep 2

# Check if token server started
if ! kill -0 $TOKEN_PID 2>/dev/null; then
    echo "Token server failed to start!"
    exit 1
fi

echo "Token server running (PID: $TOKEN_PID)"

# Start LiveKit agent (main process)
echo "Starting LiveKit agent..."
python agent.py start

# If agent exits, cleanup token server
kill $TOKEN_PID 2>/dev/null || true

