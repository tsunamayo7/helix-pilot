"""helix-pilot entry point.

Usage:
    uv run main.py              → Start MCP server (default)
    uv run main.py --cli ...    → Run CLI mode (legacy helix_pilot.py)
"""

import sys

if __name__ == "__main__":
    if "--cli" in sys.argv:
        # Legacy CLI mode
        sys.argv.remove("--cli")
        from pathlib import Path
        import runpy
        runpy.run_path(
            str(Path(__file__).parent / "scripts" / "helix_pilot.py"),
            run_name="__main__",
        )
    else:
        # MCP server mode (default)
        from server import mcp
        mcp.run()
