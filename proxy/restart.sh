#!/bin/bash

# Restart the forward proxy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Restarting proxy..."
./stop.sh
sleep 1
./start.sh
