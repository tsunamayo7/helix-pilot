# helix-pilot

**GUI automation MCP server powered by local Vision LLM (Ollama).**

helix-pilot lets AI coding agents (Claude Code, Codex CLI, etc.) see and control your Windows desktop through the [Model Context Protocol](https://modelcontextprotocol.io). It captures screenshots, analyzes them with a local Ollama Vision model, and executes mouse/keyboard actions — all running on your machine with zero cloud dependency for the vision step.

## Why helix-pilot?

| Feature | helix-pilot | UI-TARS Desktop | Peekaboo | Cua |
|---------|:-----------:|:---------------:|:--------:|:---:|
| MCP server (CLI-native) | Yes | Partial | Yes | No |
| Windows support | Yes | Yes | No (macOS) | No (VM) |
| Local Vision LLM (Ollama) | Yes | No | Yes | No |
| Host OS direct control | Yes | Yes | Yes | No (VM) |
| Open source | Yes | Yes | Yes | Yes |

## Features

- **15 MCP tools** — screenshot, click, type, hotkey, scroll, describe, find, verify, auto, browse, and more
- **Vision LLM analysis** — uses Ollama vision models to understand screen content
- **Autonomous execution** — `auto` and `browse` tools plan and execute multi-step GUI tasks
- **Safety system** — action policies, secret detection, emergency stop, user activity monitoring
- **4K/HiDPI support** — proper DPI awareness for high-resolution displays

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Ollama](https://ollama.com) with a vision model installed
- Windows 10/11

### Install a Vision Model

```bash
ollama pull mistral-small3.2
```

### Install helix-pilot

```bash
git clone https://github.com/tsunamayo7/helix-pilot.git
cd helix-pilot
uv sync
```

### Configure

Edit `config/helix_pilot.json`:

```json
{
  "ollama_endpoint": "http://localhost:11434",
  "vision_model": "mistral-small3.2:latest"
}
```

### Add to Claude Code

Add to your Claude Code MCP settings (`.claude.json` or settings):

```json
{
  "mcpServers": {
    "helix-pilot": {
      "command": "uv",
      "args": ["--directory", "/path/to/helix-pilot", "run", "server.py"]
    }
  }
}
```

### Add to Codex CLI

```json
{
  "mcpServers": {
    "helix-pilot": {
      "command": "uv",
      "args": ["--directory", "/path/to/helix-pilot", "run", "server.py"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `screenshot` | Capture screen or window screenshot |
| `click` | Click at screen coordinates |
| `type_text` | Type text (Unicode supported) |
| `hotkey` | Send keyboard shortcut (e.g. `ctrl+c`) |
| `scroll` | Scroll mouse wheel |
| `describe` | Describe screen content via Vision LLM |
| `find` | Find UI element by description, returns coordinates |
| `verify` | Verify screen matches expected state |
| `status` | Check system status (Ollama, models, screen) |
| `list_windows` | List all visible windows |
| `wait_stable` | Wait until screen stops changing |
| `auto` | Autonomous multi-step GUI task execution |
| `browse` | Browser-specialized automation |
| `click_screenshot` | Click then immediately screenshot |
| `resize_image` | Resize image for AI model size limits |

## Safety

helix-pilot includes multiple safety layers:

- **Action policies** — configurable per-site allow/deny lists
- **Immutable policy** — blocks secrets (API keys, tokens) from being typed
- **Emergency stop** — move mouse to screen corner to abort
- **User activity detection** — pauses when user is actively using the computer
- **Window deny list** — prevents interaction with sensitive windows (Task Manager, Security, etc.)
- **Execution modes** — `observe_only`, `draft_only`, `apply_with_approval`

## Architecture

```
Claude Code / Codex CLI
    |
    | MCP (stdio)
    v
server.py (FastMCP)
    |
    v
HelixPilot (scripts/helix_pilot.py)
    |
    +-- CoreOperations (PyAutoGUI + PyGetWindow)
    +-- VisionLLM (Ollama API via httpx)
    +-- SafetyGuard (policies + user monitoring)
    +-- ActionContract (policy evaluation)
```

## Development

```bash
# Run tests
uv run python -m pytest tests/ -v

# Syntax check
uv run python -m py_compile server.py

# Run server directly
uv run python server.py
```

## License

MIT
