#!/bin/bash
# Sovereign AI - Start Stack
# Launches Ollama (if needed) + Docker services + Inactivity Monitor

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Sovereign AI - Starting...${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. Ensure Ollama is running
if systemctl is-active --quiet ollama; then
    echo -e "${GREEN}[OK]${NC} Ollama service running"
else
    echo -e "${YELLOW}[..]${NC} Starting Ollama..."
    sudo systemctl start ollama
    sleep 3
    if systemctl is-active --quiet ollama; then
        echo -e "${GREEN}[OK]${NC} Ollama started"
    else
        echo -e "${RED}[!!]${NC} Failed to start Ollama"
        echo "    Check: sudo journalctl -u ollama -n 20"
        exit 1
    fi
fi

# 2. Wait for Ollama API
echo -n "  Waiting for API..."
for i in $(seq 1 15); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# 3. Start Docker stack
echo -e "${YELLOW}[..]${NC} Starting Docker services..."
cd "$DIR"
docker compose up -d 2>&1 | grep -v "^$"
echo ""

# 4. Wait for OpenWebUI health
echo -n "  Waiting for OpenWebUI..."
for i in $(seq 1 30); do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e " ${GREEN}ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# 5. Start inactivity monitor (auto-shutdown after 10 min)
echo -e "${YELLOW}[..]${NC} Starting inactivity monitor..."
"$DIR/scripts/inactivity-monitor.sh" start 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} Inactivity monitor started (10 min timeout)"
else
    echo -e "${YELLOW}[..]${NC} Inactivity monitor already running"
fi

# 6. Status report
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Sovereign AI - Online${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "  ${GREEN}OpenWebUI${NC}      http://localhost:3000"
echo -e "  ${GREEN}Open Notebook${NC}  http://localhost:8502"
echo -e "  ${GREEN}Ollama API${NC}     http://localhost:11434"
echo -e "  ${GREEN}MCP Proxy${NC}      http://localhost:8000"
echo -e "  ${GREEN}Mem0${NC}           http://localhost:8765"
echo -e "  ${GREEN}Qdrant${NC}         http://localhost:6333"

# Check if ComfyUI is available
if [ -d "$DIR/comfyui" ]; then
    if curl -s http://localhost:8188 > /dev/null 2>&1; then
        echo -e "  ${GREEN}ComfyUI${NC}        http://localhost:8188"
    else
        echo -e "  ${YELLOW}ComfyUI${NC}        not running (start: $DIR/scripts/start-comfyui.sh)"
    fi
fi
echo ""
echo -e "  Models: $(ollama list 2>/dev/null | tail -n +2 | wc -l) installed"
echo -e "  GPU:    $(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | awk -F', ' '{printf "%s/%s MB", $1, $2}')"
echo ""
echo -e "  ${YELLOW}Auto-shutdown${NC}: After 10 min inactivity"
echo -e "  Logs:   docker compose -f $DIR/docker-compose.yml logs -f"
echo ""