#!/bin/bash

# Stop the forward proxy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f proxy.pid ]; then
    echo "Proxy is not running (no PID file found)"
    exit 0
fi

PID=$(cat proxy.pid)

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Proxy process not found (stale PID file)"
    rm -f proxy.pid
    exit 0
fi

echo "Stopping proxy (PID: $PID)..."
kill "$PID"

# Wait for process to stop
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# Force kill if still running
if ps -p "$PID" > /dev/null 2>&1; then
    echo "Force killing proxy..."
    kill -9 "$PID"
fi

rm -f proxy.pid
echo "Proxy stopped."
