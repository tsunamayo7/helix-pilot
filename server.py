"""
helix-pilot MCP Server

GUI automation MCP server powered by local Vision LLM (Ollama).
Captures screenshots, clicks, types, scrolls, and analyzes screen content
using Ollama Vision models — all on your local machine.
"""

import sys
from pathlib import Path

from fastmcp import FastMCP

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pilot import create_pilot, PilotConfig

mcp = FastMCP(
    "helix-pilot",
    instructions=(
        "GUI automation MCP server powered by local Vision LLM (Ollama). "
        "Captures screenshots, clicks, types, and analyzes screen content."
    ),
)

# Lazy singleton — initialized on first tool call
_pilot = None


def _get_pilot():
    global _pilot
    if _pilot is None:
        _pilot = create_pilot()
    return _pilot


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def screenshot(
    window: str = "",
    name: str = "mcp_shot",
) -> dict:
    """Capture a screenshot of the screen or a specific window.

    Args:
        window: Target window title (substring match). Empty = full screen.
        name: Filename stem for the saved screenshot.

    Returns:
        dict with ok, path, size, and timestamp.
    """
    return _get_pilot().cmd_screenshot(window=window or None, name=name)


@mcp.tool()
def click(
    x: int,
    y: int,
    window: str = "",
    button: str = "left",
    double: bool = False,
) -> dict:
    """Click at screen coordinates.

    Args:
        x: X coordinate in pixels.
        y: Y coordinate in pixels.
        window: Target window title to activate first.
        button: Mouse button — "left", "right", or "middle".
        double: If true, perform a double-click.
    """
    return _get_pilot().cmd_click(x=x, y=y, window=window or None,
                                  button=button, double=double)


@mcp.tool()
def type_text(
    text: str,
    window: str = "",
) -> dict:
    """Type text into the focused window or a specific window.

    Args:
        text: The text to type. Supports Unicode.
        window: Target window title to activate first.
    """
    return _get_pilot().cmd_type(text=text, window=window or None)


@mcp.tool()
def hotkey(
    keys: str,
    window: str = "",
) -> dict:
    """Send a keyboard shortcut.

    Args:
        keys: Key combination, e.g. "ctrl+c", "alt+tab", "ctrl+shift+s".
        window: Target window title to activate first.
    """
    return _get_pilot().cmd_hotkey(keys=keys, window=window or None)


@mcp.tool()
def scroll(
    amount: int,
    window: str = "",
) -> dict:
    """Scroll the mouse wheel.

    Args:
        amount: Scroll amount. Positive = up, negative = down.
        window: Target window title to activate first.
    """
    return _get_pilot().cmd_scroll(amount=amount, window=window or None)


@mcp.tool()
def describe(
    window: str = "",
) -> dict:
    """Describe the current screen content using Vision LLM.

    Takes a screenshot and sends it to the local Ollama Vision model
    for analysis. Returns a natural-language description of visible
    UI elements, text, buttons, and layout.

    Args:
        window: Target window title. Empty = full screen.
    """
    return _get_pilot().cmd_describe(window=window or None)


@mcp.tool()
def find(
    description: str,
    window: str = "",
    refine: bool = False,
) -> dict:
    """Find a UI element on screen by description.

    Uses Vision LLM to locate the described element and return
    its pixel coordinates.

    Args:
        description: Natural-language description of the element to find,
                     e.g. "the Save button", "the search input field".
        window: Target window title. Empty = full screen.
        refine: If true, perform a second pass for higher accuracy.
    """
    return _get_pilot().cmd_find(
        description=description, window=window or None, refine=refine)


@mcp.tool()
def verify(
    expected: str,
    window: str = "",
) -> dict:
    """Verify that the screen matches an expected state.

    Takes a screenshot and asks the Vision LLM whether the screen
    satisfies the given condition.

    Args:
        expected: Description of the expected state,
                  e.g. "the login form is visible", "file saved successfully".
        window: Target window title. Empty = full screen.
    """
    return _get_pilot().cmd_verify(expected=expected, window=window or None)


@mcp.tool()
def status() -> dict:
    """Check helix-pilot system status.

    Returns Ollama connection status, available Vision models,
    screen resolution, and visible windows.
    """
    return _get_pilot().cmd_status()


@mcp.tool()
def list_windows() -> dict:
    """List all visible windows on the desktop.

    Returns window titles and their positions/sizes.
    """
    return _get_pilot().cmd_list_windows()


@mcp.tool()
def wait_stable(
    timeout: int = 60,
    window: str = "",
) -> dict:
    """Wait until the screen content stabilizes.

    Repeatedly captures screenshots and compares them until no changes
    are detected or timeout is reached.

    Args:
        timeout: Maximum wait time in seconds (default: 60).
        window: Target window title. Empty = full screen.
    """
    return _get_pilot().cmd_wait_stable(timeout=timeout, window=window or None)


@mcp.tool()
def auto(
    instruction: str,
    window: str = "",
    dry_run: bool = False,
) -> dict:
    """Execute an autonomous GUI task using Vision LLM.

    The Vision LLM analyzes the screen and performs a sequence of
    GUI operations to accomplish the given instruction.

    Args:
        instruction: What to do, e.g. "open Notepad and type hello".
        window: Target window title.
        dry_run: If true, plan actions without executing them.
    """
    return _get_pilot().cmd_auto(
        instruction=instruction, window=window or None, dry_run=dry_run)


@mcp.tool()
def browse(
    instruction: str,
    window: str = "",
    dry_run: bool = False,
) -> dict:
    """Execute a browser automation task using Vision LLM.

    Specialized for browser windows — navigates, clicks links,
    fills forms, and extracts information.

    Args:
        instruction: What to do in the browser, e.g. "search for Python docs".
        window: Browser window title (default: auto-detect Chrome/Edge/Firefox).
        dry_run: If true, plan actions without executing them.
    """
    return _get_pilot().cmd_browse(
        instruction=instruction, window=window or None, dry_run=dry_run)


@mcp.tool()
def click_screenshot(
    x: int,
    y: int,
    window: str = "",
    button: str = "left",
    double: bool = False,
    name: str = "click_shot",
    delay: float = 0.3,
) -> dict:
    """Click at coordinates and immediately take a screenshot.

    Useful for capturing the result of a click (e.g., opened dropdown,
    popup menu) without losing transient UI state.

    Args:
        x: X coordinate in pixels.
        y: Y coordinate in pixels.
        window: Target window title.
        button: Mouse button — "left", "right", or "middle".
        double: If true, perform a double-click.
        name: Filename stem for the screenshot.
        delay: Seconds to wait between click and screenshot (default: 0.3).
    """
    return _get_pilot().cmd_click_screenshot(
        x=x, y=y, window=window or None,
        button=button, double=double, name=name, delay=delay)


@mcp.tool()
def resize_image(
    path: str,
    max_dim: int = 1800,
    output: str = "",
) -> dict:
    """Resize an image to fit within a maximum dimension.

    Useful for pre-processing 4K screenshots before sending to AI models
    that have image size limits.

    Args:
        path: Source image file path.
        max_dim: Maximum dimension in pixels (default: 1800).
        output: Output path. Empty = append '_preview' suffix to source.
    """
    return _get_pilot().cmd_resize(
        path=path, max_dim=max_dim, output=output or None)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
