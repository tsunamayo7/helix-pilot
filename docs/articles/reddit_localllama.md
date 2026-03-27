# Reddit r/LocalLLaMA Post

**Title:**
I built an MCP server that automates any Windows desktop app using local Ollama Vision models — zero cloud API cost

**Body:**

## What it does

helix-pilot lets AI agents (Claude Code, Codex CLI, Cursor) **see and control your Windows desktop** through the Model Context Protocol, using only local Ollama vision models. No cloud APIs, no VM — just your machine.

## Demo

![MCP Tools Demo](https://raw.githubusercontent.com/tsunamayo7/helix-pilot/main/docs/demo/mcp_tools_demo.gif)

The agent calls `status()` → `screenshot()` → `describe()` → `auto()`. The local Vision LLM analyzes the screen and executes GUI actions autonomously.

## Hardware

- **Tested on:** RTX 5070 Ti (16GB VRAM), RTX PRO 6000 (96GB VRAM)
- **Minimum:** Any GPU that runs llava or moondream (~4GB VRAM)
- **CPU-only:** moondream (1.8B) works on CPU, slower but functional
- **Inference speed:** ~2-3 sec/screenshot on mistral-small3.2 (RTX 5070 Ti)

## How it works

- **FastMCP server** exposing 15 MCP tools (screenshot, click, type_text, hotkey, scroll, describe, find, verify, auto, browse, etc.)
- **Ollama Vision LLM** analyzes screenshots locally (mistral-small3.2, gemma3:27b, llava, moondream)
- **Win32 API + PyAutoGUI** for mouse/keyboard control
- **DPI-aware** — works correctly on 4K displays (3840x2160)
- **Safety system:** action policies, secret detection (blocks API keys from being typed), emergency stop (mouse to corner), user activity detection

## vs Alternatives

| Feature | helix-pilot | terminator | UI-TARS Desktop | Peekaboo | Cua |
|---------|:-----------:|:----------:|:---------------:|:--------:|:---:|
| Local Vision LLM (Ollama) | **Yes** | No | No | Yes | No |
| Windows host direct control | **Yes** | Yes | Yes | No (macOS) | No (VM) |
| MCP server (CLI-native) | **Yes** | No | Partial | Yes | No |
| Zero cloud API cost | **Yes** | No | No | **Yes** | No |
| Built-in safety system | **Yes** | Partial | No | No | Partial |

## Quick start

```bash
ollama pull mistral-small3.2
git clone https://github.com/tsunamayo7/helix-pilot.git
cd helix-pilot && uv sync
```

Add to Claude Code (`.claude.json`):
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

## Links

- **GitHub:** https://github.com/tsunamayo7/helix-pilot
- **License:** MIT
- **78 tests passing** (pytest + ruff CI)

Feedback welcome — especially interested in:
- Which Vision models work best for GUI element detection?
- What desktop apps would you want to automate?
- Any edge cases with coordinate precision on different resolutions?
