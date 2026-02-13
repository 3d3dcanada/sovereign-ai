#!/bin/bash
# Sovereign AI - Model Pull Script
# Downloads optimal models for GTX 1070 (8GB VRAM)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Sovereign AI - Model Setup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Ollama is not running${NC}"
    echo "Start it with: sudo systemctl start ollama"
    exit 1
fi

# ──────────────────────────────────────
# REMOVE OLD/UNWANTED MODELS
# ──────────────────────────────────────
echo -e "${YELLOW}Cleaning up old models...${NC}"

for model in "ministral-3:3b" "qwen2.5-coder:1.5b-base"; do
    if ollama list | grep -q "$model"; then
        echo "  Removing $model..."
        ollama rm "$model"
        echo -e "  ${GREEN}Removed $model${NC}"
    fi
done

echo ""

# ──────────────────────────────────────
# PULL OPTIMAL MODELS
# ──────────────────────────────────────
# Model selection rationale:
#
# deepseek-r1:8b (~5.2GB) — Distilled from 671B R1 model
#   Best reasoning model at 8B, chain-of-thought, research, RAG
#   VRAM: ~6.1GB with 16k ctx + q8_0 KV cache
#
# qwen3:8b (~5.2GB) — Best instruction-following 8B
#   Excellent for coding, agentic tasks, tool calling
#   Has /think and /no_think modes
#   VRAM: ~6.1GB with 16k ctx + q8_0 KV cache
#
# qwen2.5-coder:1.5b (~1GB) — Fast autocomplete
#   Perfect for tab-complete in Continue.dev
#   Small enough to run alongside an 8B model
#   VRAM: ~1.2GB
#
# nomic-embed-text:v1.5 (~300MB) — Embeddings for RAG
#   Runs on CPU, no VRAM needed
#   Best quality/size ratio for 16GB system RAM

MODELS=(
    "deepseek-r1:8b"
    "qwen3:8b"
    "qwen2.5-coder:1.5b"
    "nomic-embed-text:v1.5"
)

for model in "${MODELS[@]}"; do
    echo -e "${CYAN}Pulling $model...${NC}"
    if ollama list | grep -q "$(echo $model | cut -d: -f1)"; then
        echo -e "  ${GREEN}Already installed${NC}"
    else
        ollama pull "$model"
        echo -e "  ${GREEN}Done${NC}"
    fi
    echo ""
done

# ──────────────────────────────────────
# VERIFY
# ──────────────────────────────────────
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Installed Models${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
ollama list
echo ""

# Quick test
echo -e "${YELLOW}Quick smoke test (deepseek-r1:8b)...${NC}"
RESPONSE=$(ollama run deepseek-r1:8b "Say 'Sovereign AI online' and nothing else." 2>&1 | tail -1)
echo -e "  Response: ${GREEN}$RESPONSE${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Models ready! Total VRAM budget:${NC}"
echo -e "${GREEN}  ~6.1GB per 8B model (one at a time)${NC}"
echo -e "${GREEN}  ~1.2GB for autocomplete model${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Tip: Only one 8B model loads at a time (OLLAMA_MAX_LOADED_MODELS=1)"
echo "     Switch between deepseek-r1 and qwen3 via OpenWebUI model selector"
