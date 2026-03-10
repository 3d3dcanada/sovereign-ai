#!/bin/bash
# Sovereign AI - Startup Script
# Version: 2.0.0 - February 2026

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           SOVEREIGN AI - Local AI Workstation               ║${NC}"
echo -e "${BLUE}║                    Version 2.0.0                            ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Validate .env exists and required secrets are set
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file missing.${NC}"
    echo "  Run: cp .env.example .env && chmod 600 .env"
    echo "  Then generate secrets: openssl rand -base64 32"
    exit 1
fi
set -a; source .env; set +a
for var in WEBUI_SECRET_KEY NOTEBOOK_SECRET_KEY; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗ $var is not set in .env${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ .env validated${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}⏳ Waiting for $name to be ready...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is ready!${NC}"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e "${RED}✗ $name failed to start${NC}"
    return 1
}

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1
else
    echo -e "${YELLOW}⚠ No NVIDIA GPU detected (CPU mode)${NC}"
fi

# Pull latest images
echo ""
echo -e "${BLUE}📦 Pulling latest Docker images...${NC}"
docker compose pull 2>/dev/null || true

# Start services
echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"
docker compose up -d

# Wait for services
echo ""
wait_for_service "Ollama" "http://localhost:11434/api/tags"
wait_for_service "OpenWebUI" "http://localhost:3000/health"
wait_for_service "MCPO" "http://localhost:8000"

# Check Open Notebook
if check_port 8502; then
    echo -e "${GREEN}✓ Open Notebook is running${NC}"
fi

# Check Qdrant
if check_port 6333; then
    echo -e "${GREEN}✓ Qdrant is running${NC}"
fi

# Check Redis
if check_port 6379; then
    echo -e "${GREEN}✓ Redis is running${NC}"
fi

# Pull Ollama models if not present
echo ""
echo -e "${BLUE}🤖 Checking Ollama models...${NC}"
MODELS=("deepseek-r1:8b" "qwen3:8b" "nomic-embed-text:v1.5")
for model in "${MODELS[@]}"; do
    if ! curl -s http://localhost:11434/api/tags | grep -q "\"name\":\"$model\""; then
        echo -e "${YELLOW}  Pulling $model...${NC}"
        docker exec ollama ollama pull "$model" &
    else
        echo -e "${GREEN}  ✓ $model already pulled${NC}"
    fi
done
wait

# Print status
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           SOVEREIGN AI IS RUNNING!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  🌐 OpenWebUI:     ${GREEN}http://localhost:3000${NC}"
echo -e "  🤖 Ollama API:    ${GREEN}http://localhost:11434${NC}"
echo -e "  🔌 MCP Proxy:     ${GREEN}http://localhost:8000${NC}"
echo -e "  📓 Open Notebook: ${GREEN}http://localhost:8502${NC}"
echo -e "  🗄️ Qdrant:        ${GREEN}http://localhost:6333${NC}"
echo -e "  ⚡ Redis:         ${GREEN}localhost:6379${NC}"
echo ""
echo -e "${BLUE}MCP Servers:${NC}"
echo -e "  • filesystem    - File operations"
echo -e "  • memory        - Key-value store"
echo -e "  • brave-search  - Web search"
echo -e "  • github        - Repository operations"
echo -e "  • playwright    - Browser automation"
echo -e "  • sqlite        - Database operations"
echo -e "  • sequential-thinking - Complex reasoning"
echo ""
echo -e "${YELLOW}First time?${NC}"
echo -e "  1. Open ${GREEN}http://localhost:3000${NC} in your browser"
echo -e "  2. Create an admin account"
echo -e "  3. Configure API keys in Settings → Connections"
echo -e "  4. Install tools from ${GREEN}https://openwebui.com/tools${NC}"
echo ""
echo -e "${BLUE}To stop: ${NC}docker compose down"
echo -e "${BLUE}To view logs: ${NC}docker compose logs -f"
echo ""