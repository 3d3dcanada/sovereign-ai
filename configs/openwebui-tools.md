# OpenWebUI Community Tools to Install

Go to OpenWebUI > Workspace > Tools > + Create Tool
Or browse: https://openwebui.com/tools

## Priority Install (copy-paste the code from each link)

### 1. Code Execution Tools v2
- **What:** Run Python + shell commands safely from chat
- **URL:** https://openwebui.com/t/hub/code_execution
- **Why:** Debug code, run scripts, test snippets without leaving chat

### 2. Visuals Toolkit
- **What:** ASCII charts, tables, flowcharts, diagrams
- **URL:** https://openwebui.com/t/hub/visuals
- **Why:** Research reports, architecture diagrams, data visualization

### 3. Document Generator
- **What:** Export .docx, .xlsx, .pptx files from chat
- **URL:** https://openwebui.com/t/hub/document_generator
- **Why:** Create reports, proposals, documentation

## How to Install Any Tool

1. Open the tool URL above
2. Copy the Python code
3. In OpenWebUI: Workspace > Tools > + Create Tool
4. Paste the code, name it, save
5. Enable it in chat (toggle in sidebar or set as default)

## MCP Tools (Automatic via MCPO)

These are already configured via docker-compose + mcpo:
- **Filesystem** — Read/write/search files in /home/wess
- **Memory** — Persistent key-value store across chats
- **Time** — Current time and timezone operations

To add them in OpenWebUI:
1. Go to Admin Settings > External Tools (or Functions > External Connections)
2. Add: http://mcpo:8000 (if using Docker networking)
   Or: http://localhost:8000 (if accessing from host)
