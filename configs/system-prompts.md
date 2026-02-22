# Sovereign AI — System Prompts
# Version: 2.1.0 | February 2026

The canonical master prompt is in this same directory:
  configs/CAP_MASTER_SYSTEM_PROMPT.md

Copy it verbatim into any model's System Prompt field in OpenWebUI.

---

## HOW TO APPLY IN OPENWEBUI

### Option A — Global Default (applies to ALL models)
  Admin Panel → Settings → Interface → System Prompt
  Paste the full contents of CAP_MASTER_SYSTEM_PROMPT.md

### Option B — Per-Model (preferred — lets you tune per capability)
  Workspace → Models → [Model Name] → Edit → System Prompt
  Paste the full prompt, then add the model-specific addendum below

### Option C — Per-Chat Prompt Shortcuts
  Workspace → Prompts → + New Prompt
  Paste as a named shortcut (e.g. "/cap") so you can inject it any time

---

## MODEL-SPECIFIC ADDENDA
Paste AFTER the master prompt when configuring each model.

---

### DEEPSEEK-R1:8B — Reasoning / Research
```
## MODEL CONTEXT — DeepSeek R1 8B (Local)
- You are running locally on a GTX 1070 (8GB VRAM)
- Effective context: ~16k tokens — summarize rather than quote long docs
- Use /think for multi-step reasoning; /no_think for direct lookups
- Preferred tasks: research, planning, analysis, code review
- Constraints: no image generation; no real-time web access without tools
- When given tools: always use brave-search or fetch before citing facts
- Memory: use the memory MCP tool to persist key facts across sessions
```

---

### QWEN3:8B — Code / Build
```
## MODEL CONTEXT — Qwen3 8B (Local)
- Specialized in: Python, TypeScript/JavaScript, React, Next.js, Tailwind CSS
- Also strong in: bash, Docker, SQL, Rust basics
- Running locally — no external network unless tools are enabled
- Code style: minimal comments (only where logic isn't obvious), no over-engineering
- Always produce COMPLETE files — never truncate with "..."
- When building web UIs: default to React + Tailwind, unless stack is specified
- When writing Python: default to modern Python 3.11+, type hints, async where useful
- File access: use the filesystem MCP tool to read/write to /home/wess
```

---

### GPT-4O / CLAUDE SONNET / GEMINI — Cloud Flagship
```
## MODEL CONTEXT — Cloud Flagship Model
- You have full internet access via search tools — use them
- Preferred tasks: complex reasoning, long-form writing, vision tasks, architecture
- You have access to all MCP tools via the MCPO proxy at http://mcpo:8000
- File system access: use the filesystem tool to read/write /home/wess
- Memory: use the memory tool to persist important context
- GitHub: use the github tool for repo operations
- Web: use brave-search, fetch, and playwright for live research
- Always verify dates and versions before citing — your training has a cutoff
```

---

### NOMIC-EMBED-TEXT — Embeddings (no chat)
```
This model is for embeddings only. Do not configure a system prompt.
Used automatically by RAG and document search.
```

---

## MCPO TOOL SERVER — CONNECT TO OPENWEBUI

After starting the stack, connect MCPO tools in OpenWebUI:

  Admin Panel → Settings → Connections → Tool Servers → Add
  URL: http://mcpo:8000
  (Use http://localhost:8000 if accessing from host browser)

This gives every model access to:
  - filesystem    → read/write /home/wess/**
  - memory        → persistent key-value store
  - knowledge-graph → structured memory graph
  - brave-search  → live web search
  - fetch         → fetch any URL as markdown
  - github        → repos, issues, PRs, code search
  - context7      → live library documentation
  - playwright    → browser automation
  - sqlite        → query /app/memory/sovereign.db
  - time          → current time and timezone ops
  - sequential-thinking → step-by-step reasoning
  - system-monitor → CPU, GPU, RAM, Docker status
  - sovereign-agent → autonomous task execution
  - api-gateway   → route to any AI provider

---

## ORA BROWSER MEMORY INTEGRATION

The Ora browser extension at /home/wess/ai-workspace/ora-browser
connects to the same MCPO server. Ensure MCPO is running, then in the
Ora side panel add a custom MCP server:
  URL: http://localhost:8000
  Transport: http

Shared memory between Ora and Sovereign AI flows through:
  - MCP memory server → /app/memory/knowledge-graph.json
  - SQLite DB → /app/memory/sovereign.db
  - Qdrant vector DB → port 6333

---

## QUICK REFERENCE — KEY URLS

| Service       | URL                        | Purpose                    |
|---------------|----------------------------|----------------------------|
| OpenWebUI     | http://localhost:3000      | Primary AI chat interface  |
| MCPO          | http://localhost:8000      | MCP tool server (OpenAPI)  |
| MCPO Docs     | http://localhost:8000/docs | Tool API documentation     |
| Open Notebook | http://localhost:8502      | Research notebook          |
| Ollama        | http://localhost:11434     | Local model API            |
| Qdrant        | http://localhost:6333      | Vector DB dashboard        |
| OpenMemory    | http://localhost:8765      | Mem0 memory service        |

