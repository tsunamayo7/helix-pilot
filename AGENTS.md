# AGENTS.md — helix-pilot

## Shared Memory (Mem0)

All AI tools (Claude Code, Codex CLI, Open WebUI, Ollama) share the same Mem0 memory.

### Connection Spec (MUST match across all tools)

| Key | Value |
|-----|-------|
| Qdrant collection | `mem0_shared` |
| Qdrant URL | `http://localhost:6333` |
| Embedding model | `bge-m3` (dim=1024, via Ollama) |
| LLM for extraction | `ministral-3:8b` (via Ollama) |
| Ollama URL | `http://localhost:11434` |
| user_id | `tsunamayo7` |
| HTTP API (optional) | `http://localhost:8080` |

> **IMPORTANT**: Every tool MUST use Qdrant collection `mem0_shared`.
> Do NOT use the default collection name `mem0_mcp_selfhosted`.
> When adding a new AI tool, set `MEM0_COLLECTION=mem0_shared` explicitly.

### HTTP API (for Codex CLI, curl, scripts)

```bash
# Search
curl -s -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "search term"}'

# Add
curl -s -X POST http://localhost:8080/add \
  -H "Content-Type: application/json" \
  -d '{"text": "content to save"}'

# List all
curl -s http://localhost:8080/list
```

### MCP (for Claude Code)

Claude Code uses `mem0_mcp_bridge.py` via stdio, proxying to `localhost:8080`.
Tools: `search_memories`, `add_memory`, `get_memories`.

## Browser Use CLI 2.0

Web ブラウザ自動操作ツール。全 AI ツールから利用可能。

### Global Install

```
C:\Users\tomot\.local\bin\browser-use.exe
```

### MCP (for Claude Code)

`browser-use --mcp` (stdio) で `.claude.json` に登録済み。

### CLI (for Codex CLI, scripts)

```bash
browser-use open https://example.com
browser-use state          # ページ状態取得
browser-use click 5        # 要素クリック
browser-use input 3 "text" # テキスト入力
browser-use screenshot out.png
browser-use extract "Get all product names"
```

### Python (for Ollama)

```python
from browser_use import Agent
from browser_use import ChatOllama

llm = ChatOllama(model="gemma3:27b")
agent = Agent("search for helix-pilot on GitHub", llm=llm)
agent.run_sync()
```

### Rules

- Search for related memories at session start
- Save important decisions when user says "remember" or "save this"
- Do not save routine Q&A

## Project Info

- MCP server for local GUI automation using Ollama Vision LLM
- Language: Python 3.12, package manager: uv
- Test: `uv run pytest`
- Syntax check: `uv run python -m py_compile <file>`
