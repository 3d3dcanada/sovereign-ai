#!/bin/bash
# Sovereign AI - Update Script
# Updates Ollama, OpenWebUI, models, and MCP tools

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Sovereign AI - Update${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. Update Ollama
echo -e "${YELLOW}[1/4] Updating Ollama...${NC}"
curl -fsSL https://ollama.com/install.sh | sh 2>&1 | tail -2
echo ""

# 2. Update models
echo -e "${YELLOW}[2/4] Updating models...${NC}"
for model in deepseek-r1:8b qwen3:8b qwen2.5-coder:1.5b nomic-embed-text:v1.5; do
    echo -n "  $model... "
    ollama pull "$model" 2>&1 | tail -1
done
echo ""

# 3. Update OpenWebUI
echo -e "${YELLOW}[3/4] Updating OpenWebUI...${NC}"
cd "$DIR"
docker compose pull
docker compose up -d
echo ""

# 4. Update MCP dependencies
echo -e "${YELLOW}[4/4] Updating MCP servers...${NC}"
npm update -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-memory 2>/dev/null
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Update complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Restart with: $DIR/start.sh"
