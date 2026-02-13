#!/bin/bash
# Sovereign AI - Desktop Launcher
# Starts the stack and opens OpenWebUI in browser

DIR="$(cd "$(dirname "$0")" && pwd)"

# Start the stack
"$DIR/start.sh"

# Open browser
sleep 2
xdg-open http://localhost:3000 2>/dev/null &
