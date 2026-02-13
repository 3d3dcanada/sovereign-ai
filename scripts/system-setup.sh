#!/bin/bash
# Sovereign AI - System Setup (run with sudo)
# This script configures zswap, swap, and Ollama environment
# Usage: sudo bash ~/sovereign-ai/scripts/system-setup.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: Run with sudo${NC}"
    echo "Usage: sudo bash $0"
    exit 1
fi

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Sovereign AI - System Configuration${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ──────────────────────────────────────
# 1. ENABLE ZSWAP (compressed swap cache)
# ──────────────────────────────────────
echo -e "${YELLOW}[1/4] Configuring zswap...${NC}"

# Enable zswap now
echo "Y" > /sys/module/zswap/parameters/enabled
echo "lz4" > /sys/module/zswap/parameters/compressor 2>/dev/null || echo "lzo" > /sys/module/zswap/parameters/compressor
echo "35" > /sys/module/zswap/parameters/max_pool_percent

# Make persistent via kernel cmdline
GRUB_FILE="/etc/default/grub"
if grep -q "zswap.enabled=1" "$GRUB_FILE"; then
    echo -e "${GREEN}  zswap already in GRUB config${NC}"
else
    cp "$GRUB_FILE" "${GRUB_FILE}.bak"
    # Add zswap params to GRUB_CMDLINE_LINUX_DEFAULT
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 zswap.enabled=1 zswap.compressor=lz4 zswap.max_pool_percent=35"/' "$GRUB_FILE"
    update-grub 2>/dev/null || true
    echo -e "${GREEN}  zswap enabled and persisted in GRUB${NC}"
fi

# ──────────────────────────────────────
# 2. EXPAND SWAP TO 8GB
# ──────────────────────────────────────
echo -e "${YELLOW}[2/4] Expanding swap to 8GB...${NC}"

SWAP_FILE="/swap.img"
CURRENT_SIZE=$(stat -f --printf="%s" "$SWAP_FILE" 2>/dev/null || stat --printf="%s" "$SWAP_FILE" 2>/dev/null || echo "0")
TARGET_SIZE=$((8 * 1024 * 1024 * 1024))  # 8GB

if [ "$CURRENT_SIZE" -ge "$TARGET_SIZE" ]; then
    echo -e "${GREEN}  Swap already >= 8GB${NC}"
else
    echo "  Turning off current swap..."
    swapoff "$SWAP_FILE" 2>/dev/null || true
    echo "  Creating 8GB swap file (this may take a moment)..."
    fallocate -l 8G "$SWAP_FILE" || dd if=/dev/zero of="$SWAP_FILE" bs=1M count=8192 status=progress
    chmod 600 "$SWAP_FILE"
    mkswap "$SWAP_FILE"
    swapon "$SWAP_FILE"
    echo -e "${GREEN}  Swap expanded to 8GB${NC}"
fi

# Lower swappiness for desktop responsiveness (only swap when needed)
echo "10" > /proc/sys/vm/swappiness
if ! grep -q "vm.swappiness=10" /etc/sysctl.conf; then
    echo "vm.swappiness=10" >> /etc/sysctl.conf
fi
echo -e "${GREEN}  Swappiness set to 10${NC}"

# ──────────────────────────────────────
# 3. CONFIGURE OLLAMA SERVICE
# ──────────────────────────────────────
echo -e "${YELLOW}[3/4] Configuring Ollama service...${NC}"

OLLAMA_OVERRIDE="/etc/systemd/system/ollama.service.d/override.conf"
mkdir -p "$(dirname $OLLAMA_OVERRIDE)"

cat > "$OLLAMA_OVERRIDE" << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KEEP_ALIVE=5m"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
EOF

systemctl daemon-reload
systemctl restart ollama
sleep 3

echo -e "${GREEN}  Ollama configured with:${NC}"
echo "    - KV cache: q8_0 (halves VRAM for context)"
echo "    - Flash attention: enabled"
echo "    - Keep alive: 5m (auto-unload idle models)"
echo "    - Max loaded: 1 (prevents VRAM overflow)"

# ──────────────────────────────────────
# 4. VERIFY
# ──────────────────────────────────────
echo -e "${YELLOW}[4/4] Verifying...${NC}"

echo ""
echo -e "${CYAN}  Zswap:${NC}"
echo "    Enabled: $(cat /sys/module/zswap/parameters/enabled)"
echo "    Compressor: $(cat /sys/module/zswap/parameters/compressor)"
echo "    Max pool: $(cat /sys/module/zswap/parameters/max_pool_percent)%"

echo ""
echo -e "${CYAN}  Swap:${NC}"
swapon --show

echo ""
echo -e "${CYAN}  Swappiness:${NC} $(cat /proc/sys/vm/swappiness)"

echo ""
echo -e "${CYAN}  Ollama:${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "    ${GREEN}Running and responsive${NC}"
else
    echo -e "    ${YELLOW}Restarting...${NC}"
    sleep 5
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "    ${GREEN}Running after restart${NC}"
    else
        echo -e "    ${RED}Not responding - check: journalctl -u ollama${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  System configuration complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next: Run ~/sovereign-ai/scripts/pull-models.sh to download models"
