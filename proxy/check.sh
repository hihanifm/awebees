#!/bin/bash

# Check proxy status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Proxy Status ==="
echo ""

# Load configuration
if [ -f config.env ]; then
    source config.env
    echo "Configuration:"
    echo "  Target: ${TARGET_PROTOCOL}://${TARGET_HOST}:${TARGET_PORT}"
    echo "  Listen: ${LISTEN_HOST:-0.0.0.0}:${LISTEN_PORT}"
    echo ""
else
    echo "Warning: config.env not found"
    echo ""
fi

# Check if running
if [ -f proxy.pid ]; then
    PID=$(cat proxy.pid)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Status: RUNNING (PID: $PID)"
        
        # Test connectivity
        if [ -n "$LISTEN_PORT" ]; then
            if command -v nc &> /dev/null; then
                if nc -z localhost "$LISTEN_PORT" 2>/dev/null; then
                    echo "Port ${LISTEN_PORT}: LISTENING"
                else
                    echo "Port ${LISTEN_PORT}: NOT LISTENING (process running but port not accessible)"
                fi
            else
                echo "Port ${LISTEN_PORT}: (nc not available, cannot test)"
            fi
        fi
    else
        echo "Status: NOT RUNNING (stale PID file)"
        rm -f proxy.pid
    fi
else
    echo "Status: NOT RUNNING"
fi

echo ""
