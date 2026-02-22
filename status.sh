#!/bin/bash
# Sovereign AI - Status Dashboard

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}${BOLD}========================================${NC}"
echo -e "${CYAN}${BOLD}  Sovereign AI - Status${NC}"
echo -e "${CYAN}${BOLD}========================================${NC}"
echo ""

# Services
echo -e "${BOLD}Services${NC}"
echo -e "────────────────────────────────────────"

check() {
    local name="$1" url="$2" port="$3"
    if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} $name (port $port)"
    else
        echo -e "  ${RED}[--]${NC} $name (port $port)"
    fi
}

check "Ollama"        "http://localhost:11434/api/tags" "11434"
check "OpenWebUI"     "http://localhost:3000"           "3000"
check "Open Notebook" "http://localhost:8502"           "8502"
check "MCP Proxy"     "http://localhost:8000"           "8000"
check "Mem0"          "http://localhost:8765"           "8765"
check "Qdrant"        "http://localhost:6333"           "6333"
check "Redis"         "http://localhost:6379"           "6379"
check "ComfyUI"       "http://localhost:8188"           "8188"
echo ""

# Inactivity Monitor
echo -e "${BOLD}Inactivity Monitor${NC}"
echo -e "────────────────────────────────────────"
if [ -f "$DIR/logs/inactivity-monitor.pid" ]; then
    PID=$(cat "$DIR/logs/inactivity-monitor.pid")
    if kill -0 "$PID" 2>/dev/null; then
        if [ -f "$DIR/logs/.last-activity" ]; then
            LAST=$(cat "$DIR/logs/.last-activity")
            NOW=$(date +%s)
            ELAPSED=$((NOW - LAST))
            REMAINING=$((600 - ELAPSED))
            MINS=$((REMAINING / 60))
            SECS=$((REMAINING % 60))
            echo -e "  ${GREEN}[OK]${NC} Running (PID: $PID)"
            echo -e "  Auto-shutdown in: ${YELLOW}${MINS}m ${SECS}s${NC}"
        else
            echo -e "  ${GREEN}[OK]${NC} Running (PID: $PID)"
        fi
    else
        echo -e "  ${RED}[--]${NC} Not running (stale PID)"
    fi
else
    echo -e "  ${YELLOW}[--]${NC} Not running"
fi
echo ""

# GPU
echo -e "${BOLD}GPU${NC}"
echo -e "────────────────────────────────────────"
nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu,utilization.gpu --format=csv,noheader 2>/dev/null | \
    awk -F', ' '{printf "  %s\n  VRAM: %s / %s MB | Temp: %s C | Load: %s\n", $1, $2, $3, $4, $5}'
echo ""

# Memory
echo -e "${BOLD}System Memory${NC}"
echo -e "────────────────────────────────────────"
free -h | awk 'NR==2{printf "  RAM:  %s / %s (%.0f%% used)\n", $3, $2, $3/$2*100}'
free -h | awk 'NR==3{printf "  Swap: %s / %s\n", $3, $2}'

ZSWAP=$(cat /sys/module/zswap/parameters/enabled 2>/dev/null)
if [ "$ZSWAP" = "Y" ]; then
    ZSWAP_SIZE=$(awk '/^Zswap:/{printf "%.1f MB", $2/1024}' /proc/meminfo)
    echo -e "  Zswap: ${GREEN}enabled${NC} ($ZSWAP_SIZE compressed)"
else
    echo -e "  Zswap: ${YELLOW}disabled${NC}"
fi
echo ""

# Models
echo -e "${BOLD}Models${NC}"
echo -e "────────────────────────────────────────"
if ollama list 2>/dev/null | tail -n +2 | while read -r line; do
    NAME=$(echo "$line" | awk '{print $1}')
    SIZE=$(echo "$line" | awk '{print $3, $4}')
    echo "  $NAME ($SIZE)"
done; then
    true
else
    echo -e "  ${RED}Ollama not responding${NC}"
fi
echo ""

# Docker
echo -e "${BOLD}Docker${NC}"
echo -e "────────────────────────────────────────"
docker ps --format "  {{.Names}}\t{{.Status}}" 2>/dev/null || echo -e "  ${RED}Docker not running${NC}"
echo ""

# Disk
echo -e "${BOLD}Disk${NC}"
echo -e "────────────────────────────────────────"
df -h / | awk 'NR==2{printf "  Root: %s / %s (%s used)\n", $3, $2, $5}'
du -sh ~/.ollama/models 2>/dev/null | awk '{printf "  Ollama models: %s\n", $1}'
echo ""
echo -e "${CYAN}========================================${NC}"