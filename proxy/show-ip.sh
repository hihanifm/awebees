#!/bin/bash

# Show proxy connection information

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Proxy Connection Information ==="
echo ""

# Load configuration
if [ -f config.env ]; then
    source config.env
    echo "Proxy is configured to listen on: ${LISTEN_HOST:-0.0.0.0}:${LISTEN_PORT:-8080}"
    echo ""
fi

echo "To connect to the proxy, use one of these addresses:"
echo ""

# Localhost (same machine)
echo "1. From this machine (localhost):"
echo "   http://localhost:${LISTEN_PORT:-8080}"
echo "   http://127.0.0.1:${LISTEN_PORT:-8080}"
echo ""

# Network IP
OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
    # macOS
    NETWORK_IP=$(ifconfig | grep -E "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
elif [[ "$OS" == "Linux" ]]; then
    # Linux
    NETWORK_IP=$(ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    if [ -z "$NETWORK_IP" ]; then
        NETWORK_IP=$(hostname -I | awk '{print $1}')
    fi
fi

if [ -n "$NETWORK_IP" ]; then
    echo "2. From other devices on your network:"
    echo "   http://${NETWORK_IP}:${LISTEN_PORT:-8080}"
    echo ""
    echo "   Your machine's IP address: $NETWORK_IP"
else
    echo "2. Network IP: Could not determine (check your network settings)"
fi

echo ""
echo "=== Example Client Configuration ==="
echo ""

# Show examples based on detected IP
PROXY_URL="http://localhost:${LISTEN_PORT:-8080}"
if [ -n "$NETWORK_IP" ]; then
    NETWORK_PROXY_URL="http://${NETWORK_IP}:${LISTEN_PORT:-8080}"
fi

echo "Python (OpenAI):"
echo "  proxies = {"
echo "      'http': '$PROXY_URL',"
echo "      'https': '$PROXY_URL'"
echo "  }"
echo ""

echo "cURL:"
echo "  curl -x $PROXY_URL https://api.openai.com/v1/models \\"
echo "    -H 'Authorization: Bearer YOUR_API_KEY'"
echo ""

echo "Environment Variables:"
echo "  export HTTP_PROXY=$PROXY_URL"
echo "  export HTTPS_PROXY=$PROXY_URL"
echo ""

if [ -n "$NETWORK_IP" ]; then
    echo "For network access (from other devices):"
    echo "  Use: $NETWORK_PROXY_URL"
fi
