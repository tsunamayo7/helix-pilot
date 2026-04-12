# Hacker News Show HN Submission

**Title:**
Show HN: helix-pilot – MCP server for Windows desktop automation with local Ollama Vision

**URL:**
https://github.com/tsunamayo7/helix-pilot

**Text (optional, for self-post):**

helix-pilot is an MCP server that lets AI agents see and control Windows desktop applications using local Ollama Vision models.

The problem: Browser automation is solved (Playwright, etc.), but there's no good way for AI agents to interact with native desktop apps (Premiere Pro, Excel, Settings) without cloud Vision APIs.

helix-pilot captures screenshots via Win32 API, sends them to a local Ollama Vision model (mistral-small3.2, gemma3, moondream), and executes mouse/keyboard actions based on the LLM's analysis. 20 MCP tools including screenshot, describe, find, click, type_text, hotkey, scroll, auto, browse, verify, plus persistent background agent lifecycle tools (spawn_pilot_agent, send_pilot_agent_input, etc.).

Key design decisions:
- 100% local inference via Ollama (zero cloud cost, no data leaves your machine)
- Direct host OS control via Win32 API (not a VM)
- Built-in safety: action policies + secret scrubbing (details in README)
- Works with Claude Code, Cursor, Codex CLI, or any MCP client

Tech: Python 3.12, FastMCP, PyAutoGUI, Win32 API. MIT license.

https://github.com/tsunamayo7/helix-pilot
