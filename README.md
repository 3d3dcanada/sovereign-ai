# Sovereign AI - Local AI Workstation

**Version 2.0.0** | February 2026

A fully-featured, self-hosted AI workstation with autonomous agent capabilities, MCP server integration, and multi-provider API support.

---

## 🚀 Quick Start

```bash
# 1. Navigate to project directory
cd /home/wess/sovereign-ai

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
./scripts/start.sh
```

**Access OpenWebUI:** http://localhost:3000

---

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| **OpenWebUI** | 3000 | Main AI interface |
| **Ollama** | 11434 | Local LLM inference |
| **MCPO** | 8000 | MCP OpenAPI Proxy |
| **Mem0** | 8765 | Memory service with Qdrant |
| **Open Notebook** | 8502 | Research notebook |
| **Qdrant** | 6333 | Vector database |
| **Redis** | 6379 | Caching layer |

---

## 🤖 Local Models

Pre-configured models (auto-pulled on first start):

- `deepseek-r1:8b` - Reasoning model
- `qwen3:8b` - General purpose
- `nomic-embed-text:v1.5` - Embeddings

---

## 🔌 MCP Servers

### Core Servers (via MCPO)
| Server | Purpose |
|--------|---------|
| `filesystem` | File read/write/search |
| `memory` | Key-value store |
| `knowledge-graph` | Persistent knowledge graph |
| `time` | Time operations |
| `brave-search` | Web search |
| `github` | Repository operations |
| `playwright` | Browser automation |
| `puppeteer` | Alternative browser |
| `sequential-thinking` | Complex reasoning |
| `sqlite` | Database operations |
| `fetch` | HTTP requests |

### Custom Servers
| Server | Purpose |
|--------|---------|
| `shell-confirm` | Shell commands with safety tiers |
| `sovereign-agent` | Autonomous agent with task execution |

---

## 🌐 API Providers

Configure in `.env`:

| Provider | Models | Use Case |
|----------|--------|----------|
| **NVIDIA NIM** | DeepSeek R1, Qwen, Nemotron | Frontier models (free tier) |
| **Groq** | Llama 70B, DeepSeek R1 | Fast inference |
| **Google AI** | Gemini 2.5 | Long documents |
| **Mistral** | Codestral | Coding |
| **OpenAI** | GPT-4o, DALL-E | General + images |
| **Anthropic** | Claude | Advanced reasoning |
| **OpenRouter** | All models | Aggregator |

---

## 🛠️ Tools

### Community Tools (`tools/community/`)
- `code_execution.py` - Run Python/shell code
- `web_search.py` - Brave Search integration
- `image_generation.py` - DALL-E/Stability AI with vision support

### Custom Tools (`tools/custom/`)
- `system_control.py` - System monitoring

### Installing Tools in OpenWebUI
1. Go to **Workspace → Tools**
2. Click **+** to add a new tool
3. Paste the tool code
4. Save and enable

---

## 🤖 Autonomous Agent

The Sovereign Agent is a fully functional autonomous AI agent:

### Features
- Plan → Act → Observe → Reflect loop
- Real tool execution (shell, file, web, memory)
- Memory persistence
- Human confirmation for dangerous actions

### Safety Tiers
| Tier | Examples | Behavior |
|------|----------|----------|
| **SAFE** | `ls`, `cat`, `grep` | Auto-execute |
| **MODERATE** | `git status`, `docker ps` | Log + execute |
| **ELEVATED** | `npm install`, `docker run` | Notify + execute |
| **DANGEROUS** | `rm -rf`, `sudo` | **Require confirmation** |

### Starting the Agent
```bash
# Start with agent profile
docker compose --profile agent up -d
```

---

## 📝 OpenWebUI Functions

### Filters (`functions/filters/`)
- `safety_filter.py` - Content safety filtering

### Pipes (`functions/pipes/`)
- `memory_pipe.py` - Mem0/Qdrant integration

### Actions (`functions/actions/`)
- `quick_actions.py` - Summarize, export, search, execute

---

## 📁 Project Structure

```
sovereign-ai/
├── docker-compose.yml          # All services
├── Dockerfile.mcpo             # MCP proxy image
├── .env                        # API keys (gitignored)
├── .env.example                # Template
├── configs/
│   ├── mcpo-config.json        # MCP servers
│   ├── api-providers.yaml      # API configurations
│   └── continue-config.json    # VS Code integration
├── mcp-servers/
│   ├── shell-confirm/          # Shell with confirmation
│   └── sovereign-agent/        # Autonomous agent
├── tools/
│   ├── community/              # OpenWebUI tools
│   └── custom/                 # Custom tools
├── functions/
│   ├── filters/                # Message filters
│   ├── pipes/                  # Response transformers
│   └── actions/                # User-triggered actions
├── scripts/
│   ├── start.sh                # Start services
│   └── update.sh               # Update all
├── data/
│   ├── rag-docs/               # RAG documents
│   ├── notebook/               # Open Notebook data
│   ├── memory/                 # Mem0 data
│   └── images/                 # Generated images
└── logs/
    └── audit/                  # Command logs
```

---

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Search
BRAVE_API_KEY=your-key

# AI Providers
NVIDIA_API_KEY=your-key
GROQ_API_KEY=your-key
GOOGLE_API_KEY=your-key
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
MISTRAL_API_KEY=your-key

# Developer Tools
GITHUB_TOKEN=your-token
```

### VS Code Integration

Copy the Continue.dev config:

```bash
mkdir -p ~/.continue
cp configs/continue-config.json ~/.continue/config.json
```

---

## 📚 Resources

- **OpenWebUI Docs:** https://docs.openwebui.com
- **OpenWebUI Community:** https://openwebui.com
- **MCP Servers:** https://mcp-awesome.com
- **NVIDIA NIM:** https://build.nvidia.com
- **Ollama:** https://ollama.ai
- **Mem0:** https://mem0.ai

---

## 🔄 Updates

```bash
./scripts/update.sh
```

This will:
1. Pull latest Docker images
2. Rebuild custom images
3. Update Ollama models
4. Restart services

---

## 🛑 Stop Services

```bash
docker compose down
```

---

## 📝 License

MIT License - Use freely for personal and commercial projects.

---

## 🙏 Credits

- OpenWebUI Team
- Ollama Team
- Anthropic (MCP)
- NVIDIA (NIM)
- Mem0
- All MCP server contributors