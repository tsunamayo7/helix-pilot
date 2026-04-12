# Reddit r/LocalLLaMA Post (v2 — Use Case Focused)

**Title:**
Local Ollama Vision + Windows GUI automation via MCP (zero cloud, daily use)

**Body:**

Hey r/LocalLLaMA!

I've been using local vision models (mistral-small3.2, gemma3:27b) to automate desktop apps on Windows through MCP (Model Context Protocol). Thought I'd share my setup since the "zero cloud cost" aspect fits the spirit of this sub.

## What this does

My MCP server, **helix-pilot**, lets AI agents (Claude Code, Cursor, Codex CLI) see my screen and control any Windows application using local Ollama Vision models.

**Real workflows I use daily:**

- Tell Claude Code: "Open the file in Premiere Pro and trim the first 5 seconds" → it screenshots, finds the timeline, clicks, drags
- "Check cell B5 in the open Excel sheet" → screenshots, reads the value via Vision LLM, reports back
- "Open Settings and check my display resolution" → navigates Windows Settings app

No cloud API calls. All inference runs on my local GPU.

## Hardware

- **Daily driver:** RTX 5070 Ti (16GB) with mistral-small3.2 — ~2-3 sec per screenshot analysis
- **For complex UIs:** RTX PRO 6000 (96GB) with gemma3:27b — more accurate but slower
- **Budget option:** moondream (1.8B) works on CPU or 4GB VRAM GPUs

## How it works

```
AI Agent → MCP → helix-pilot → Ollama Vision → Win32 API
```

1. Agent requests screenshot
2. helix-pilot captures via Win32 API (DPI-aware, works on 4K)
3. Ollama Vision model analyzes the screenshot
4. Agent decides what to do (click, type, hotkey)
5. helix-pilot executes via SendInput

20 MCP tools total: screenshot, click, type_text, hotkey, scroll, describe, find, verify, status, list_windows, wait_stable, auto, browse, click_screenshot, resize_image, plus five `*_pilot_agent` tools for running background GUI workers (spawn / send_input / wait / list / close).

## Safety (important for desktop automation)

helix-pilot ships with a couple of safeguards documented in the README:

- **Action policies**: configurable per-site allow/deny lists for click/type/submit/publish
- **Secret scrubbing**: immutable policy blocks typing from sensitive paths (`.env`, `secrets/`) and flags API-key-shaped strings

Additional runtime layers (emergency-stop corner, user activity detection) live in the `SafetyGuard` module for anyone who wants to dig into the code.

## Quick start

```bash
ollama pull mistral-small3.2
git clone https://github.com/tsunamayo7/helix-pilot.git
cd helix-pilot && uv sync
```

Then add to your MCP client config and go.

## vs other tools

| | helix-pilot | Peekaboo (macOS only) | Cua | Computer Use |
|--|:-:|:-:|:-:|:-:|
| Windows host | **Yes** | No | No (VM) | Yes |
| Local LLM | **Yes** | Yes | No | No |
| MCP native | **Yes** | Yes | No | No |
| Free | **Yes** | Yes | No | No |

---

**GitHub:** https://github.com/tsunamayo7/helix-pilot

Happy to answer questions about the Vision LLM integration, prompt engineering for UI analysis, or the safety system. What models are you all using for vision tasks?
