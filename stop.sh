#!/bin/bash
# Sovereign AI - Stop Stack
# Stops Docker services + Inactivity Monitor

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}Sovereign AI - Stopping...${NC}"
echo ""

# Stop inactivity monitor first
if [ -f "$DIR/logs/inactivity-monitor.pid" ]; then
    echo -e "${YELLOW}[..]${NC} Stopping inactivity monitor..."
    "$DIR/scripts/inactivity-monitor.sh" stop 2>/dev/null
    echo -e "${GREEN}[OK]${NC} Inactivity monitor stopped"
fi

# Stop Docker services
cd "$DIR"
docker compose down 2>/dev/null
echo -e "${GREEN}[OK]${NC} Docker services stopped"

# Optionally stop Ollama (usually leave it running)
if [ "$1" = "--all" ]; then
    sudo systemctl stop ollama
    echo -e "${GREEN}[OK]${NC} Ollama stopped"
else
    echo -e "  Ollama left running (use --all to stop everything)"
fi

echo ""
echo -e "${GREEN}Stopped.${NC} Restart with: $DIR/start.sh"