#!/bin/bash
# Helper script to kill any lingering web server processes

PORT=${1:-5000}

echo "🔍 Looking for processes on port $PORT..."

PIDS=$(lsof -ti:$PORT 2>/dev/null)

if [ -z "$PIDS" ]; then
    echo "✅ No processes found on port $PORT"
else
    echo "💀 Killing processes: $PIDS"
    echo $PIDS | xargs kill -TERM 2>/dev/null || true
    sleep 1
    
    # Check if processes are still running
    REMAINING=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$REMAINING" ]; then
        echo "🔨 Force killing stubborn processes: $REMAINING"
        echo $REMAINING | xargs kill -KILL 2>/dev/null || true
    fi
    
    echo "✅ Port $PORT should now be free"
fi