#!/bin/bash

# View proxy logs in a readable format

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Proxy Logs Viewer ==="
echo ""
echo "1. Access Logs (HTTP requests)"
echo "2. Error Logs (Caddy errors)"
echo "3. Both (tail -f)"
echo "4. Clear logs"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "=== Access Logs (last 50 lines) ==="
        if [ -f logs/access.log ]; then
            # Try to parse JSON logs if jq is available
            if command -v jq &> /dev/null; then
                tail -50 logs/access.log | jq -r 'if .request then "\(.request.method) \(.request.uri) - \(.status) - \(.duration)ms" else . end' 2>/dev/null || tail -50 logs/access.log
            else
                tail -50 logs/access.log
            fi
        else
            echo "No access logs found."
        fi
        ;;
    2)
        echo ""
        echo "=== Error Logs (last 50 lines) ==="
        if [ -f logs/caddy.log ]; then
            tail -50 logs/caddy.log | grep -i error || echo "No errors found in recent logs."
        else
            echo "No error logs found."
        fi
        ;;
    3)
        echo ""
        echo "=== Following logs (Ctrl+C to exit) ==="
        if command -v jq &> /dev/null; then
            tail -f logs/access.log | jq -r 'if .request then "\(.request.method) \(.request.uri) - \(.status)" else . end' 2>/dev/null &
            TAIL_PID=$!
            tail -f logs/caddy.log &
            wait $TAIL_PID
        else
            tail -f logs/access.log logs/caddy.log
        fi
        ;;
    4)
        echo ""
        read -p "Are you sure you want to clear all logs? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            > logs/access.log
            > logs/caddy.log
            echo "Logs cleared."
        else
            echo "Cancelled."
        fi
        ;;
    *)
        echo "Invalid option."
        exit 1
        ;;
esac
