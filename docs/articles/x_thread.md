# X (Twitter) Thread — 7 tweets

## Tweet 1 (Hook)
I built an MCP server that lets Claude Code see and control my Windows desktop.

No cloud APIs. No VM. Just local Ollama Vision LLM.

Here's how it works (and you can try it now):

🧵

## Tweet 2 (Problem)
The problem:

Browser automation? Solved (Playwright, Puppeteer).

But what about Premiere Pro? Excel? Any native Windows app?

Existing tools are either:
- macOS only (Peekaboo)
- VM-based (Cua)
- Cloud API dependent ($$$)

I wanted: local, Windows-native, MCP.

## Tweet 3 (Solution + Demo)
helix-pilot = MCP server + local Vision LLM

1. Captures screenshot
2. Ollama analyzes what's on screen
3. Executes mouse/keyboard actions
4. All on YOUR machine

15 MCP tools: screenshot, click, type, find, auto, browse...

[ATTACH: mcp_tools_demo.gif]

## Tweet 4 (Safety)
GUI automation without safety = disaster.

helix-pilot has 6 safety layers:

🛑 Emergency stop (mouse to corner)
🔐 Secret detection (blocks API keys)
🚫 Window deny list (protects Task Manager)
✅ Action validation before execution
📋 Execution modes (observe → draft → approve)
👤 Pauses when you're using the PC

## Tweet 5 (Zero cost)
Zero cost to run:

- Ollama: free
- Vision models: mistral-small3.2, gemma3:27b, llava
- No API keys needed
- No data leaves your PC
- Works on 4GB VRAM (llava) to 96GB (qwen3.5:122b)

Tested on RTX 5070 Ti — ~2 sec per screenshot analysis.

## Tweet 6 (MCP compatibility)
Works with any MCP client:

- Claude Code
- Codex CLI
- Cursor / VS Code
- Open WebUI (via MCPO proxy)

3 commands to start:

ollama pull mistral-small3.2
git clone github.com/tsunamayo7/helix-pilot
cd helix-pilot && uv sync

## Tweet 7 (CTA)
helix-pilot is MIT licensed and open source.

78 tests, CI green, v1.0.0 released.

GitHub: github.com/tsunamayo7/helix-pilot

⭐ Star if you find it useful.

What desktop app would you automate first?
