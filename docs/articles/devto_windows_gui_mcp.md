---
title: "Building an MCP Server for Windows Desktop GUI Automation with Local Vision LLM"
published: true
description: "How I built helix-pilot: an MCP server that lets AI agents see and control Windows desktop apps using local Ollama Vision models — zero cloud API cost"
tags: mcp, ollama, python, automation
cover_image: https://raw.githubusercontent.com/tsunamayo7/helix-pilot/main/docs/demo/architecture.png
---

A few weeks ago, I saw [kwin-mcp](https://github.com/isac322/kwin-mcp) — an MCP server for Linux desktop GUI automation on KDE Plasma Wayland. Great project. But I'm on Windows, and I wanted something that:

1. **Controls the host OS directly** (not a VM)
2. **Uses local Vision LLMs** (zero cloud API cost)
3. **Works as an MCP server** (plug into Claude Code, Cursor, Codex CLI)

Nothing existed for this combination. So I built **helix-pilot**.

## The Problem

Browser automation is solved — Playwright, Puppeteer, Selenium. But what about:
- **Premiere Pro** timeline editing
- **Excel** formula debugging
- **Any native Windows app** that doesn't have an API

Existing GUI automation tools have trade-offs:

| Tool | Limitation |
|------|-----------|
| Peekaboo | macOS only |
| Cua | Runs inside a VM |
| UI-TARS Desktop | Not CLI-native, no local LLM |
| Computer Use (Claude/GPT) | Cloud API required |

## How helix-pilot Works

```
Claude Code  ──MCP──▶  helix-pilot  ──▶  Win32 API
                            │
                     Ollama Vision LLM
                     (local, no cloud)
```

1. **Screenshot**: Captures the screen via Win32 API (DPI-aware, 4K ready)
2. **Analyze**: Sends screenshot to local Ollama Vision model
3. **Plan**: LLM generates action plan (click coordinates, text to type, hotkeys)
4. **Execute**: Win32 SendInput / PyAutoGUI performs the actions
5. **Verify**: Takes another screenshot to confirm success

All 20 MCP tools are exposed through FastMCP:

```
screenshot, click, type_text, hotkey, scroll,
describe, find, verify, status, list_windows,
wait_stable, auto, browse, click_screenshot, resize_image,
spawn_pilot_agent, send_pilot_agent_input, wait_pilot_agent,
list_pilot_agents, close_pilot_agent
```

## Quick Start

```bash
# 1. Get a Vision model
ollama pull mistral-small3.2

# 2. Clone and install
git clone https://github.com/tsunamayo7/helix-pilot.git
cd helix-pilot && uv sync

# 3. Add to your MCP client config
```

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "helix-pilot": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/helix-pilot", "python", "server.py"]
    }
  }
}
```

Now in Claude Code:

```
> Open Notepad and type "Hello from helix-pilot!"
```

The agent captures the screen, analyzes it with Vision LLM, finds Notepad, clicks, and types — all locally.

## Vision Model Performance

Tested on my RTX 5070 Ti (16GB VRAM):

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| moondream (1.8B) | ~2GB | Fast | ★★ |
| mistral-small3.2 (7B) | ~5GB | Medium | ★★★★ |
| gemma3:27b | ~16GB | Slower | ★★★★★ |

Even moondream works on CPU-only machines — slower but functional.

## Safety Features

GUI automation is powerful, so helix-pilot ships with a couple of safeguards out of the box:

- **Action policies**: Per-site allow/deny lists control which actions (click, type, submit, publish) are permitted in each context
- **Secret scrubbing**: The immutable policy blocks typing content from sensitive paths (`.env`, `secrets/`, etc.) and flags API-key-shaped strings

More details on both are in the README. Additional layers (emergency stop corner, user activity monitoring) are implemented in the runtime and discussed in the repo — see the `SafetyGuard` module if you want to dig in.

## helix-pilot vs kwin-mcp

Since kwin-mcp inspired this post, here's how they compare:

| Feature | helix-pilot | kwin-mcp |
|---------|:-----------:|:--------:|
| OS | **Windows** | Linux (KDE) |
| Vision LLM | **Ollama local** | None (accessibility tree) |
| MCP Tools | 20 | Dozens (accessibility tree based) |
| Isolation | Host direct | Isolated KWin session |
| AI Understanding | Sees the screen | Reads DOM/a11y tree |

Different approaches for different platforms. kwin-mcp uses accessibility tree (fast, precise). helix-pilot uses Vision LLM (works with any app, even those without accessibility support).

## What's Next

- Linux support (via xdotool/ydotool)
- macOS support (via cliclick/screencapture)
- Multi-monitor coordination
- Vision model fine-tuning for UI elements

**Star the repo if this is useful:**
[github.com/tsunamayo7/helix-pilot](https://github.com/tsunamayo7/helix-pilot)

---

*Built by [tsunamayo7](https://github.com/tsunamayo7) — a developer building local-first AI tools.*
