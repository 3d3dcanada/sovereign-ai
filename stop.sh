#!/bin/bash
# Sovereign AI - Stop Stack

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}Sovereign AI - Stopping...${NC}"
echo ""

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
