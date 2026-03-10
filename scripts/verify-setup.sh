#!/bin/bash
# Sovereign AI - Setup Verification Script
# Run this to verify all components are properly configured

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo -e "${CYAN}${BOLD}========================================${NC}"
echo -e "${CYAN}${BOLD}  Sovereign AI - Setup Verification${NC}"
echo -e "${CYAN}${BOLD}========================================${NC}"
echo ""

errors=0
warnings=0

check_file() {
    local file="$1"
    local desc="$2"
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}[OK]${NC} $desc"
    else
        echo -e "  ${RED}[--]${NC} $desc"
        ((errors++))
    fi
}

check_exec() {
    local file="$1"
    local desc="$2"
    if [ -x "$file" ]; then
        echo -e "  ${GREEN}[OK]${NC} $desc (executable)"
    else
        echo -e "  ${YELLOW}[!!]${NC} $desc (not executable)"
        ((warnings++))
    fi
}

check_dir() {
    local dir="$1"
    local desc="$2"
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}[OK]${NC} $desc"
    else
        echo -e "  ${RED}[--]${NC} $desc"
        ((errors++))
    fi
}

# Main Scripts
echo -e "${BOLD}Main Scripts${NC}"
echo -e "────────────────────────────────────────"
check_exec "$DIR/sovereign-ai.sh" "Desktop Launcher"
check_exec "$DIR/start.sh" "Start Script"
check_exec "$DIR/stop.sh" "Stop Script"
check_exec "$DIR/status.sh" "Status Script"
check_exec "$DIR/scripts/inactivity-monitor.sh" "Inactivity Monitor"
echo ""

# Configuration
echo -e "${BOLD}Configuration${NC}"
echo -e "────────────────────────────────────────"
check_file "$DIR/docker-compose.yml" "Docker Compose"
check_file "$DIR/configs/mcpo-config.json" "MCPO Config"
check_file "$DIR/.env.example" "Environment Example"
check_file "$DIR/Dockerfile.mcpo" "MCPO Dockerfile"
echo ""

# MCP Servers
echo -e "${BOLD}MCP Servers${NC}"
echo -e "────────────────────────────────────────"
check_file "$DIR/mcp-servers/sovereign-agent/agent.py" "Sovereign Agent"
check_file "$DIR/mcp-servers/sovereign-agent/Dockerfile" "Sovereign Agent Dockerfile"
check_file "$DIR/mcp-servers/shell-confirm/server.py" "Shell Confirm"
check_file "$DIR/mcp-servers/system-monitor/server.py" "System Monitor"
check_file "$DIR/mcp-servers/api-gateway/server.py" "API Gateway"
echo ""

# Sovereign Agent Modules
echo -e "${BOLD}Sovereign Agent Modules${NC}"
echo -e "────────────────────────────────────────"
check_file "$DIR/mcp-servers/sovereign-agent/prompts/__init__.py" "Prompts Module"
check_file "$DIR/mcp-servers/sovereign-agent/prompts/system_prompts.py" "System Prompts"
check_file "$DIR/mcp-servers/sovereign-agent/safety/__init__.py" "Safety Module"
check_file "$DIR/mcp-servers/sovereign-agent/safety/classifier.py" "Safety Classifier"
check_file "$DIR/mcp-servers/sovereign-agent/safety/audit.py" "Safety Audit"
check_file "$DIR/mcp-servers/sovereign-agent/safety/confirmation.py" "Safety Confirmation"
check_file "$DIR/mcp-servers/sovereign-agent/tools/__init__.py" "Tools Module"
check_file "$DIR/mcp-servers/sovereign-agent/tools/base.py" "Tools Base"
check_file "$DIR/mcp-servers/sovereign-agent/tools/shell.py" "Shell Tool"
check_file "$DIR/mcp-servers/sovereign-agent/tools/file.py" "File Tool"
check_file "$DIR/mcp-servers/sovereign-agent/tools/web.py" "Web Tool"
check_file "$DIR/mcp-servers/sovereign-agent/tools/memory.py" "Memory Tool"
check_file "$DIR/mcp-servers/sovereign-agent/tools/docker.py" "Docker Tool"
echo ""

# Desktop Entry
echo -e "${BOLD}Desktop Entry${NC}"
echo -e "────────────────────────────────────────"
check_file "$HOME/.local/share/applications/sovereign-ai.desktop" "Desktop File"
check_file "$DIR/sovereign-ai-icon.png" "Icon"
echo ""

# Directories
echo -e "${BOLD}Directories${NC}"
echo -e "────────────────────────────────────────"
check_dir "$DIR/logs" "Logs Directory"
check_dir "$DIR/data" "Data Directory"
check_dir "$DIR/configs" "Configs Directory"
echo ""

# Docker
echo -e "${BOLD}Docker Status${NC}"
echo -e "────────────────────────────────────────"
if docker info &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} Docker is running"
    containers=$(docker ps --format "{{.Names}}" 2>/dev/null | wc -l)
    echo -e "  Running containers: $containers"
else
    echo -e "  ${YELLOW}[!!]${NC} Docker not running (start with: sudo systemctl start docker)"
    ((warnings++))
fi
echo ""

# Ollama
echo -e "${BOLD}Ollama Status${NC}"
echo -e "────────────────────────────────────────"
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    echo -e "  ${GREEN}[OK]${NC} Ollama is running"
    models=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    echo -e "  Models installed: $models"
else
    echo -e "  ${YELLOW}[!!]${NC} Ollama not running (start with: sudo systemctl start ollama)"
    ((warnings++))
fi
echo ""

# Summary
echo -e "${CYAN}${BOLD}========================================${NC}"
echo -e "${CYAN}${BOLD}  Verification Complete${NC}"
echo -e "${CYAN}${BOLD}========================================${NC}"
echo ""
if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}All setup checks passed!${NC}"
    echo ""
    echo "Runtime status is separate. Start Sovereign AI with:"
    echo "  - Click the desktop icon, or"
    echo "  - Run: $DIR/sovereign-ai.sh"
    echo ""
    echo "Then verify live services with:"
    echo "  - $DIR/status.sh"
    echo ""
    echo "Included capabilities:"
    echo "  - Auto-shutdown after 10 minutes of inactivity"
    echo "  - MCP server integration"
    echo "  - Safety tier system for command execution"
else
    echo -e "${RED}Errors: $errors${NC}"
    echo -e "${YELLOW}Warnings: $warnings${NC}"
    echo ""
    if [ $errors -gt 0 ]; then
        echo "Please fix the errors above before running."
    fi
fi
echo ""
