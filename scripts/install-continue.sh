#!/bin/bash
# Sovereign AI - Install & Configure Continue.dev for VS Code
# Provides local AI coding assistance (autocomplete + chat)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Continue.dev Setup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. Install Continue.dev extension
echo -e "${YELLOW}[1/2] Installing Continue.dev VS Code extension...${NC}"
if code --list-extensions 2>/dev/null | grep -qi "continue"; then
    echo -e "  ${GREEN}Already installed${NC}"
else
    code --install-extension Continue.continue 2>/dev/null && \
        echo -e "  ${GREEN}Installed${NC}" || \
        echo -e "  ${YELLOW}Install manually: Search 'Continue' in VS Code Extensions${NC}"
fi
echo ""

# 2. Copy config
echo -e "${YELLOW}[2/2] Configuring Continue.dev...${NC}"
CONTINUE_DIR="$HOME/.continue"
mkdir -p "$CONTINUE_DIR"

if [ -f "$CONTINUE_DIR/config.json" ]; then
    cp "$CONTINUE_DIR/config.json" "$CONTINUE_DIR/config.json.bak"
    echo "  Backed up existing config to config.json.bak"
fi

cp "$DIR/configs/continue-config.json" "$CONTINUE_DIR/config.json"
echo -e "  ${GREEN}Config installed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Continue.dev Ready${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Usage in VS Code:"
echo "  - Tab autocomplete: Just type (uses Qwen2.5-Coder 1.5B)"
echo "  - Chat: Ctrl+L (uses DeepSeek-R1 or Qwen3)"
echo "  - Edit: Ctrl+I (inline edit with AI)"
echo "  - @workspace: Reference your entire project"
echo ""
echo "Models:"
echo "  - DeepSeek-R1 8B  → Best for reasoning, explaining code"
echo "  - Qwen3 8B        → Best for writing code, refactoring"
echo "  - Qwen2.5-Coder   → Fast autocomplete (always running)"
