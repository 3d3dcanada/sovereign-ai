#!/bin/bash
# Sovereign AI - Update Script
# Version: 2.0.0 - February 2026

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           SOVEREIGN AI - Update Script                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Pull latest Docker images
echo -e "${BLUE}📦 Pulling latest Docker images...${NC}"
docker compose pull

# Rebuild custom images
echo -e "${BLUE}🔨 Rebuilding custom images...${NC}"
docker compose build --no-cache mcpo

# Update Ollama models
echo -e "${BLUE}🤖 Updating Ollama models...${NC}"
MODELS=("deepseek-r1:8b" "qwen3:8b" "nomic-embed-text:v1.5")
for model in "${MODELS[@]}"; do
    echo -e "${YELLOW}  Updating $model...${NC}"
    docker exec ollama ollama pull "$model"
done

# Restart services
echo -e "${BLUE}🔄 Restarting services...${NC}"
docker compose down
docker compose up -d

echo ""
echo -e "${GREEN}✓ Update complete!${NC}"
echo -e "${BLUE}Run ${NC}./scripts/start.sh${BLUE} to verify services.${NC}"