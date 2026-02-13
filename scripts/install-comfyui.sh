#!/bin/bash
# Sovereign AI - ComfyUI Installation
# Native install (not Docker) for direct GPU access on GTX 1070
# Uses --lowvram mode for 8GB VRAM

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'
DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMFY_DIR="$DIR/comfyui"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  ComfyUI Installation${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. System dependencies
echo -e "${YELLOW}[1/5] Checking dependencies...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Python3 not found. Install with: sudo apt install python3 python3-venv python3-pip${NC}"
    exit 1
fi

# 2. Clone ComfyUI
echo -e "${YELLOW}[2/5] Installing ComfyUI...${NC}"
if [ -d "$COMFY_DIR" ]; then
    echo "  Updating existing install..."
    cd "$COMFY_DIR" && git pull
else
    echo "  Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

# 3. Create venv and install deps
echo -e "${YELLOW}[3/5] Setting up Python environment...${NC}"
cd "$COMFY_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 4. Install GGUF support (for quantized image models)
echo -e "${YELLOW}[4/5] Installing GGUF support...${NC}"
if [ ! -d "$COMFY_DIR/custom_nodes/ComfyUI-GGUF" ]; then
    cd "$COMFY_DIR/custom_nodes"
    git clone https://github.com/city96/ComfyUI-GGUF.git
    cd ComfyUI-GGUF
    pip install -r requirements.txt
fi

# 5. Create launcher script
echo -e "${YELLOW}[5/5] Creating launcher...${NC}"
cat > "$DIR/scripts/start-comfyui.sh" << 'LAUNCHER'
#!/bin/bash
# Start ComfyUI with low-VRAM optimizations for GTX 1070
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR/comfyui"
source venv/bin/activate

echo "Starting ComfyUI on http://localhost:8188"
echo "NOTE: Unload LLM models first for best performance"
echo "      (Ollama auto-unloads after 5min idle)"
echo ""

python main.py \
    --listen 0.0.0.0 \
    --port 8188 \
    --lowvram \
    --preview-method auto \
    --force-fp16 \
    "$@"
LAUNCHER
chmod +x "$DIR/scripts/start-comfyui.sh"

deactivate

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ComfyUI Installed${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Start ComfyUI:  ~/sovereign-ai/scripts/start-comfyui.sh"
echo "Web UI:          http://localhost:8188"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Download an image model (Z-Image-Turbo GGUF recommended):"
echo "     Place GGUF models in: $COMFY_DIR/models/unet/"
echo "     Place VAE models in:  $COMFY_DIR/models/vae/"
echo "     Place CLIP models in: $COMFY_DIR/models/text_encoders/"
echo ""
echo "  2. Connect to OpenWebUI:"
echo "     Admin Settings > Images > Engine: ComfyUI"
echo "     API URL: http://localhost:8188"
echo ""
echo -e "${YELLOW}VRAM note:${NC} ComfyUI shares the GPU with Ollama."
echo "  Ollama auto-unloads models after 5min idle."
echo "  For best image gen speed, wait for Ollama to unload or stop it."
