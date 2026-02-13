# Sovereign AI

A fully local, private AI workstation optimized for GTX 1070 (8GB VRAM).
Blazing fast quantized models, agentic tool use, RAG knowledge base, and coding assistance — all running on your hardware.

## Hardware Target

| Component | Spec |
|-----------|------|
| GPU | NVIDIA GTX 1070 (8GB VRAM, Pascal) |
| CPU | Intel i7-7700 (4C/8T, 4.2GHz boost) |
| RAM | 16GB DDR4 |
| Storage | 480GB SSD (primary) |
| OS | Ubuntu 24.04.3 LTS |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOU (Browser)                            │
│         :3000 OpenWebUI    |    :8502 Open Notebook             │
└──────────────┬─────────────────────────┬───────────────────────┘
               │                         │
┌──────────────▼─────────────┐  ┌────────▼────────────────────────┐
│  OpenWebUI (Docker :3000)  │  │  Open Notebook (Docker :8502)   │
│  Chat, RAG, Tools, Code    │  │  Project notes, PDFs, research  │
│  Execution, Web Search     │  │  AI-powered organization        │
└──────┬───────────┬─────────┘  └────────┬────────────────────────┘
       │           │                     │
┌──────▼───────┐  ┌▼─────────────────┐   │
│ Ollama       │  │ MCPO Proxy :8000 │   │
│ :11434       │  │ MCP → OpenAPI    │   │
│              │◄─┤                  │◄──┘
│ deepseek-r1  │  │ Filesystem       │
│ qwen3:8b     │  │ Memory           │
│ qwen2.5-coder│  │ Time             │
│ nomic-embed  │  └──────────────────┘
└──────┬───────┘
       │
┌──────▼───────┐
│ Continue.dev │
│ (VS Code)    │
│ Autocomplete │
└──────────────┘
```

## Models

| Model | Size | VRAM | Speed | Role |
|-------|------|------|-------|------|
| **deepseek-r1:8b** | 5.2 GB | ~6.1 GB | 40-55 t/s | Reasoning, research, RAG |
| **qwen3:8b** | 5.2 GB | ~6.1 GB | 45-60 t/s | Coding, tool calling, agentic |
| **qwen2.5-coder:1.5b** | 1 GB | ~1.2 GB | 80+ t/s | Tab autocomplete |
| **nomic-embed-text:v1.5** | 300 MB | CPU | - | Embeddings for RAG |

Only **one 8B model loads at a time** (auto-swapped by Ollama). The 1.5B autocomplete model can run alongside.

## Quick Start

### 1. System Setup (one time, needs sudo)

```bash
sudo bash ~/sovereign-ai/scripts/system-setup.sh
```

Configures: zswap, 8GB swap, Ollama environment (q8_0 KV cache, flash attention)

### 2. Pull Models (one time)

```bash
bash ~/sovereign-ai/scripts/pull-models.sh
```

### 3. Start Everything

```bash
~/sovereign-ai/start.sh
```

### 4. Open

- **OpenWebUI:** http://localhost:3000
- **Open Notebook:** http://localhost:8502
- **Ollama API:** http://localhost:11434
- **MCP Proxy:** http://localhost:8000

## Management

```bash
~/sovereign-ai/start.sh          # Start all services
~/sovereign-ai/stop.sh            # Stop Docker (Ollama stays)
~/sovereign-ai/stop.sh --all      # Stop everything
~/sovereign-ai/status.sh          # Dashboard
~/sovereign-ai/scripts/update.sh  # Update all components
```

## Ollama Optimizations

| Setting | Value | Why |
|---------|-------|-----|
| `OLLAMA_KV_CACHE_TYPE` | `q8_0` | Halves context VRAM with ~0 quality loss |
| `OLLAMA_FLASH_ATTENTION` | `1` | Faster attention computation |
| `OLLAMA_KEEP_ALIVE` | `5m` | Auto-unload idle models |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Prevents VRAM overflow |

## RAG (Knowledge Base)

Upload documents in OpenWebUI to build a local knowledge base:
1. Go to OpenWebUI > Workspace > Knowledge
2. Create a collection (e.g., "Textbooks", "Research")
3. Upload PDFs, markdown, text files
4. The model will reference these when answering questions

Settings: 512-token chunks, 100-token overlap, nomic-embed-text:v1.5 embeddings, DuckDuckGo web search enabled.

## MCP Tools (Agentic Capabilities)

Via the MCPO proxy, your models can:
- **Filesystem:** Read, write, search files in your home directory
- **Memory:** Persistent key-value store across chat sessions
- **Time:** Get current time, timezone operations

Add more servers by editing `configs/mcpo-config.json`.

## VS Code Integration (Continue.dev)

```bash
bash ~/sovereign-ai/scripts/install-continue.sh
```

- **Tab autocomplete:** Qwen2.5-Coder 1.5B (always running, 80+ t/s)
- **Chat (Ctrl+L):** DeepSeek-R1 or Qwen3 (switch in sidebar)
- **Inline edit (Ctrl+I):** AI-powered code editing
- **@workspace:** Reference your entire project

## Free Cloud Fallbacks

For tasks that need more power than local 8B models:

| Provider | Free Tier | Best For |
|----------|-----------|----------|
| [Groq](https://console.groq.com) | 14,400 req/day | Fast inference, large models |
| [Google AI Studio](https://aistudio.google.com) | 250K tok/min | Long documents (Gemini) |
| [Mistral](https://console.mistral.ai) | 1B tok/month | Heavy coding (Codestral) |

See `configs/free-cloud-apis.md` for setup instructions.

## File Structure

```
~/sovereign-ai/
├── docker-compose.yml              # OpenWebUI + MCPO + Open Notebook
├── start.sh                        # Start all services
├── stop.sh                         # Stop services
├── status.sh                       # Status dashboard
├── sovereign-ai.sh                 # Desktop launcher (opens browser)
├── sovereign-ai-icon.png           # Application icon
├── configs/
│   ├── mcpo-config.json            # MCP server definitions
│   ├── continue-config.json        # VS Code Continue.dev config
│   ├── system-prompts.md           # Prompts for OpenWebUI
│   ├── openwebui-tools.md          # Community tools to install
│   └── free-cloud-apis.md          # Cloud API setup guide
├── scripts/
│   ├── system-setup.sh             # System config (sudo)
│   ├── pull-models.sh              # Download models
│   ├── install-continue.sh         # VS Code setup
│   └── update.sh                   # Update everything
├── docs/
│   └── walkthrough.html            # Interactive setup guide
├── data/
│   ├── rag-docs/                   # Drop documents here for RAG
│   ├── notebook/                   # Open Notebook app data
│   └── notebook-db/                # Open Notebook database
└── logs/                           # Service logs
```

## Portability

This setup is designed to be portable:
- All config is in version-controlled files (no hidden state)
- Docker volumes are named (`sovereign-ai-webui-data`) for easy backup/restore
- Ollama models are stored in `~/.ollama/models/` (standard location)
- Clone this repo + run `system-setup.sh` + `pull-models.sh` on any Ubuntu machine with an NVIDIA GPU

### Backup

```bash
# Backup OpenWebUI data
docker run --rm -v sovereign-ai-webui-data:/data -v $(pwd):/backup alpine tar czf /backup/webui-backup.tar.gz /data

# Backup Ollama models
tar czf ollama-models-backup.tar.gz ~/.ollama/models/
```

### Restore on New Machine

```bash
git clone <your-repo-url> ~/sovereign-ai
cd ~/sovereign-ai
sudo bash scripts/system-setup.sh
bash scripts/pull-models.sh
./start.sh
```

## Open Notebook (Project Organization)

Access at http://localhost:8502 after starting the stack.

Open Notebook is an AI-powered research notebook for organizing projects, PDFs, and notes:
- Upload documents (PDFs, text, web pages) and get AI-powered summaries
- Organize by project with searchable notebooks
- Full-text and vector search across all content
- Connect to your local Ollama models for analysis

Configure Ollama connection in Open Notebook's settings after first launch.

## Limitations (8GB VRAM)

- Max practical context: 16k-24k tokens (not the model's full 128k)
- One 8B model at a time (auto-swapped, ~2s switch)
- No simultaneous image generation + chat
- Reranking may be slow on the i7-7700 (disable if >4s latency)

## Open Source Projects Used

This stack is built entirely on open source software:

| Project | Role | License | Repository |
|---------|------|---------|------------|
| [Ollama](https://ollama.com) | Local LLM runtime | MIT | [github.com/ollama/ollama](https://github.com/ollama/ollama) |
| [Open WebUI](https://openwebui.com) | Chat interface, RAG, tools | MIT | [github.com/open-webui/open-webui](https://github.com/open-webui/open-webui) |
| [Open Notebook](https://open-notebook.ai) | AI research notebook | MIT | [github.com/lfnovo/open-notebook](https://github.com/lfnovo/open-notebook) |
| [MCPO](https://github.com/open-webui/mcpo) | MCP-to-OpenAPI proxy | MIT | [github.com/open-webui/mcpo](https://github.com/open-webui/mcpo) |
| [Continue.dev](https://continue.dev) | VS Code AI coding | Apache 2.0 | [github.com/continuedev/continue](https://github.com/continuedev/continue) |
| [DeepSeek-R1](https://huggingface.co/deepseek-ai/DeepSeek-R1) | Reasoning model | MIT | [huggingface.co/deepseek-ai](https://huggingface.co/deepseek-ai/DeepSeek-R1) |
| [Qwen3](https://huggingface.co/Qwen/Qwen3-8B) | Coding/agentic model | Apache 2.0 | [huggingface.co/Qwen](https://huggingface.co/Qwen/Qwen3-8B) |
| [Qwen2.5-Coder](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) | Autocomplete model | Apache 2.0 | [huggingface.co/Qwen](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B) |
| [Nomic Embed Text](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) | Embeddings for RAG | Apache 2.0 | [huggingface.co/nomic-ai](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) |
| [MCP Servers](https://modelcontextprotocol.io) | Agentic tool servers | MIT | [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| [Docker](https://docker.com) | Container runtime | Apache 2.0 | [github.com/moby/moby](https://github.com/moby/moby) |

## License

MIT
