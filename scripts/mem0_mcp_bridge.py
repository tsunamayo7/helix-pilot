"""Memory MCP Bridge — lightweight proxy to shared memory HTTP API.

Bridges MCP (stdio JSON-RPC) to the shared memory HTTP server at localhost:8080.
Backend: Qdrant direct + Ollama embedding (qdrant_memory_server.py).
Timeout: 30s per request to prevent hanging.
"""

import json
import sys
import io
import urllib.request
import urllib.error
from os import environ

# Windows 環境で stdin/stdout の UTF-8 を強制
if sys.platform == "win32":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", newline="\n")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# MCP JSON-RPC over stdio implementation (no external deps)

MEM0_URL = environ.get("MEM0_HTTP_URL", "http://localhost:8080")
MEM0_USER_ID = environ.get("MEM0_USER_ID", "tsunamayo7")
TIMEOUT = int(environ.get("MEM0_TIMEOUT", "30"))

TOOLS = [
    {
        "name": "search_memories",
        "description": "Semantic search across existing memories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language description of what to find."},
                "limit": {"type": "integer", "description": "Maximum number of results."},
                "user_id": {"type": "string", "description": "User scope."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "add_memory",
        "description": "Store a new memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The memory content to store."},
                "user_id": {"type": "string", "description": "User scope."},
                "metadata": {"type": "object", "description": "Optional metadata."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "get_memories",
        "description": "Page through memories using filters instead of search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User scope."},
                "limit": {"type": "integer", "description": "Maximum number of memories to return."},
            },
        },
    },
]


def http_post(path: str, body: dict) -> dict:
    """POST to Mem0 HTTP API with timeout."""
    url = f"{MEM0_URL}{path}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": f"HTTP request failed: {e}"}
    except TimeoutError:
        return {"error": f"Timeout after {TIMEOUT}s"}


def http_get(path: str) -> dict:
    """GET from Mem0 HTTP API with timeout."""
    url = f"{MEM0_URL}{path}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": f"HTTP request failed: {e}"}
    except TimeoutError:
        return {"error": f"Timeout after {TIMEOUT}s"}


def handle_tool(name: str, args: dict) -> str:
    """Execute a tool and return the result as a string."""
    user_id = args.get("user_id") or MEM0_USER_ID

    if name == "search_memories":
        body = {"query": args["query"], "user_id": user_id}
        if args.get("limit"):
            body["limit"] = args["limit"]
        result = http_post("/search", body)
        return json.dumps({"results": result if isinstance(result, list) else result})

    elif name == "add_memory":
        body = {"text": args["text"], "user_id": user_id}
        if args.get("metadata"):
            body["metadata"] = args["metadata"]
        result = http_post("/add", body)
        return json.dumps(result)

    elif name == "get_memories":
        result = http_get("/list")
        return json.dumps(result)

    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


def write_msg(msg: dict) -> None:
    """Write a JSON-RPC message to stdout."""
    raw = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(raw + "\n")
    sys.stdout.flush()


def make_response(id, result):
    return {"jsonrpc": "2.0", "id": id, "result": result}


def main():
    sys.stderr.write(f"mem0-mcp-bridge: started (backend={MEM0_URL}, timeout={TIMEOUT}s)\n")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            write_msg(make_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mem0-bridge", "version": "1.0.0"},
                "instructions": (
                    "Memory tools for persistent cross-session memory. "
                    "Use search_memories to find relevant context before starting work. "
                    "Use add_memory to store important facts, preferences, and decisions. "
                    "Use get_memories to browse stored memories."
                ),
            }))

        elif method == "notifications/initialized":
            pass  # no response needed

        elif method == "tools/list":
            write_msg(make_response(msg_id, {"tools": TOOLS}))

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            try:
                result_text = handle_tool(tool_name, tool_args)
                write_msg(make_response(msg_id, {
                    "content": [{"type": "text", "text": result_text}],
                }))
            except Exception as e:
                write_msg(make_response(msg_id, {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                }))

        elif method == "ping":
            write_msg(make_response(msg_id, {}))

        elif msg_id is not None:
            write_msg({"jsonrpc": "2.0", "id": msg_id, "error": {
                "code": -32601, "message": f"Method not found: {method}",
            }})


if __name__ == "__main__":
    main()
