#!/bin/bash
# Sovereign AI - Desktop Launcher
# Starts the stack and opens OpenWebUI in browser
# Auto-shuts down after 10 minutes of inactivity

DIR="$(cd "$(dirname "$0")" && pwd)"

# Create logs directory if needed
mkdir -p "$DIR/logs"

echo "=========================================="
echo "  Sovereign AI - Desktop Launcher"
echo "=========================================="
echo ""

# Start the stack (includes inactivity monitor)
"$DIR/start.sh"

# Check if startup was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "Failed to start Sovereign AI. Check logs for details."
    read -p "Press Enter to close..."
    exit 1
fi

# Open browser
echo ""
echo "Opening browser..."
sleep 2
xdg-open http://localhost:3000 2>/dev/null &

echo ""
echo "=========================================="
echo "  Sovereign AI is running!"
echo "=========================================="
echo ""
echo "  The backend will auto-shutdown after"
echo "  10 minutes of inactivity."
echo ""
echo "  To keep running, use the interface."
echo "  To stop manually: $DIR/stop.sh"
echo ""