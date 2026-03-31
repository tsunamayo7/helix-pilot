"""
helix-pilot MCP Server

GUI automation MCP server powered by local Vision LLM (Ollama).
Captures screenshots, clicks, types, scrolls, and analyzes screen content
using Ollama Vision models — all on your local machine.
"""

import asyncio
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pilot import create_pilot  # noqa: E402

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


PILOT_AGENT_ROLE_HINTS = {
    "default": (
        "You are a general GUI automation agent. Complete the requested task "
        "safely and return a concise operational summary."
    ),
    "explorer": (
        "You are a read-heavy GUI explorer agent. Prefer observing, planning, "
        "and verifying state over making changes."
    ),
    "worker": (
        "You are an execution-focused GUI worker agent. Perform the task "
        "directly, verify the outcome, and summarize the result."
    ),
}


def _normalize_pilot_agent_type(agent_type: str) -> str:
    return agent_type if agent_type in PILOT_AGENT_ROLE_HINTS else "default"


def _default_pilot_dry_run(agent_type: str) -> bool:
    return _normalize_pilot_agent_type(agent_type) == "explorer"


def _summarize_pilot_result(result: dict) -> str:
    if not isinstance(result, dict):
        return str(result)[:800]
    parts: list[str] = []
    command = result.get("command")
    if command:
        parts.append(f"command={command}")
    if "summary" in result and result["summary"]:
        parts.append(str(result["summary"]))
    if "detail" in result and result["detail"]:
        parts.append(str(result["detail"]))
    if "description" in result and result["description"]:
        parts.append(str(result["description"]))
    if "error" in result and result["error"]:
        parts.append(f"error={result['error']}")
    if "steps_succeeded" in result and "steps_executed" in result:
        parts.append(
            f"steps={result.get('steps_succeeded', 0)}/{result.get('steps_executed', 0)}"
        )
    if not parts:
        parts.append(str(result))
    return " | ".join(parts)[:1200]


@dataclass
class PilotAgentTurn:
    instruction: str
    task_mode: str
    window: str
    dry_run: bool
    success: bool
    summary: str
    result: dict
    finished_at: float


@dataclass
class PilotAgentRecord:
    agent_id: str
    description: str
    agent_type: str
    task_mode: str
    window: str
    dry_run: bool
    created_at: float
    updated_at: float
    status: str = "idle"
    last_instruction: str = ""
    last_summary: str = ""
    last_result: dict = field(default_factory=dict)
    last_success: Optional[bool] = None
    history: list[PilotAgentTurn] = field(default_factory=list)
    current_task: Optional[asyncio.Task] = field(default=None, repr=False)
    closed: bool = False


class PilotAgentManager:
    def __init__(self, max_agents: int = 16):
        self._agents: dict[str, PilotAgentRecord] = {}
        self._order: list[str] = []
        self._max_agents = max_agents

    def create(
        self,
        description: str,
        agent_type: str,
        task_mode: str,
        window: str,
        dry_run: bool,
    ) -> PilotAgentRecord:
        now = time.time()
        agent = PilotAgentRecord(
            agent_id=f"pilot-{uuid.uuid4().hex[:8]}",
            description=description.strip(),
            agent_type=_normalize_pilot_agent_type(agent_type),
            task_mode=task_mode if task_mode in {"auto", "browse"} else "auto",
            window=window,
            dry_run=dry_run,
            created_at=now,
            updated_at=now,
        )
        self._agents[agent.agent_id] = agent
        self._order.append(agent.agent_id)
        self._trim_idle_agents()
        return agent

    def _trim_idle_agents(self) -> None:
        if len(self._order) <= self._max_agents:
            return
        removable: list[str] = []
        for agent_id in self._order:
            agent = self._agents.get(agent_id)
            if not agent:
                removable.append(agent_id)
                continue
            if agent.current_task is None and (agent.closed or agent.status in {"completed", "failed"}):
                removable.append(agent_id)
            if len(self._order) - len(removable) <= self._max_agents:
                break
        for agent_id in removable:
            self._agents.pop(agent_id, None)
            if agent_id in self._order:
                self._order.remove(agent_id)

    def get(self, agent_id: str) -> Optional[PilotAgentRecord]:
        return self._agents.get(agent_id)

    def list_all(self) -> list[PilotAgentRecord]:
        return [self._agents[agent_id] for agent_id in reversed(self._order) if agent_id in self._agents]

    def _build_instruction(self, agent: PilotAgentRecord, instruction: str) -> str:
        sections = [PILOT_AGENT_ROLE_HINTS[agent.agent_type]]
        if agent.description:
            sections.append(f"Agent description:\n{agent.description}")
        if agent.history:
            prior = []
            for turn in agent.history[-3:]:
                prior.append(f"- Previous instruction: {turn.instruction[:300]}")
                prior.append(f"  Result summary: {turn.summary[:600]}")
            sections.append("Prior GUI context:\n" + "\n".join(prior))
        sections.append(f"Current GUI task:\n{instruction.strip()}")
        return "\n\n".join(sections)

    async def _run_turn(self, agent: PilotAgentRecord, instruction: str) -> None:
        agent.status = "running"
        agent.updated_at = time.time()
        agent.last_instruction = instruction
        pilot = _get_pilot()
        full_instruction = self._build_instruction(agent, instruction)
        try:
            if agent.task_mode == "browse":
                result = await asyncio.to_thread(
                    pilot.cmd_browse,
                    full_instruction,
                    agent.window or None,
                    agent.dry_run,
                )
            else:
                result = await asyncio.to_thread(
                    pilot.cmd_auto,
                    full_instruction,
                    agent.window or None,
                    agent.dry_run,
                )
            success = bool(result.get("ok", False)) if isinstance(result, dict) else False
            summary = _summarize_pilot_result(result if isinstance(result, dict) else {"result": result})
            agent.last_result = result if isinstance(result, dict) else {"result": result}
            agent.last_summary = summary
            agent.last_success = success
            agent.history.append(
                PilotAgentTurn(
                    instruction=instruction,
                    task_mode=agent.task_mode,
                    window=agent.window,
                    dry_run=agent.dry_run,
                    success=success,
                    summary=summary,
                    result=agent.last_result,
                    finished_at=time.time(),
                )
            )
            agent.status = "completed" if success else "failed"
        except asyncio.CancelledError:
            agent.status = "closed"
            agent.last_success = False
            agent.last_summary = "Agent run was cancelled before completion."
            agent.last_result = {"ok": False, "error": agent.last_summary}
            raise
        finally:
            agent.updated_at = time.time()
            agent.current_task = None

    def start(self, agent: PilotAgentRecord, instruction: str) -> PilotAgentRecord:
        if agent.closed:
            raise ValueError("Agent is already closed.")
        if agent.current_task is not None:
            raise ValueError("Agent is already running.")
        agent.current_task = asyncio.create_task(self._run_turn(agent, instruction))
        return agent

    async def wait(self, agent: PilotAgentRecord, timeout: int) -> dict:
        if agent.current_task is None:
            return self.snapshot(agent)
        try:
            await asyncio.wait_for(asyncio.shield(agent.current_task), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        return self.snapshot(agent)

    def close(self, agent: PilotAgentRecord) -> PilotAgentRecord:
        if agent.current_task is not None:
            raise ValueError("Agent is still running. Wait for completion before closing it.")
        agent.closed = True
        agent.status = "closed"
        agent.updated_at = time.time()
        return agent

    def snapshot(self, agent: PilotAgentRecord) -> dict:
        return {
            "ok": True,
            "agent_id": agent.agent_id,
            "description": agent.description,
            "agent_type": agent.agent_type,
            "task_mode": agent.task_mode,
            "window": agent.window,
            "dry_run": agent.dry_run,
            "status": agent.status,
            "closed": agent.closed,
            "history_count": len(agent.history),
            "last_instruction": agent.last_instruction,
            "last_summary": agent.last_summary,
            "last_success": agent.last_success,
            "last_result": agent.last_result,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at,
        }


pilot_agents = PilotAgentManager()


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
    result = _get_pilot().cmd_status()
    if isinstance(result, dict):
        agents = pilot_agents.list_all()
        result = dict(result)
        result["agent_runtime"] = {
            "tracked_agents": len(agents),
            "running_agents": sum(1 for agent in agents if agent.current_task is not None),
        }
    return result


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
# Agent lifecycle tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def spawn_pilot_agent(
    instruction: str,
    description: str = "",
    agent_type: str = "worker",
    task_mode: str = "auto",
    window: str = "",
    dry_run: bool | None = None,
) -> dict:
    """Start a background helix-pilot agent for auto or browse workflows."""
    resolved_type = _normalize_pilot_agent_type(agent_type)
    resolved_dry_run = _default_pilot_dry_run(resolved_type) if dry_run is None else dry_run
    agent = pilot_agents.create(
        description=description,
        agent_type=resolved_type,
        task_mode=task_mode,
        window=window,
        dry_run=resolved_dry_run,
    )
    pilot_agents.start(agent, instruction)
    return pilot_agents.snapshot(agent)


@mcp.tool()
async def send_pilot_agent_input(
    agent_id: str,
    instruction: str,
) -> dict:
    """Continue an existing helix-pilot agent with a follow-up instruction."""
    agent = pilot_agents.get(agent_id)
    if not agent:
        return {"ok": False, "error": f"Unknown agent_id: {agent_id}"}
    try:
        pilot_agents.start(agent, instruction)
    except ValueError as e:
        return {"ok": False, "error": str(e), "agent_id": agent_id}
    return pilot_agents.snapshot(agent)


@mcp.tool()
async def wait_pilot_agent(
    agent_id: str,
    timeout: int = 30,
) -> dict:
    """Wait for a background helix-pilot agent to finish its current turn."""
    agent = pilot_agents.get(agent_id)
    if not agent:
        return {"ok": False, "error": f"Unknown agent_id: {agent_id}"}
    return await pilot_agents.wait(agent, timeout)


@mcp.tool()
async def list_pilot_agents() -> dict:
    """List all tracked helix-pilot background agents."""
    agents = [pilot_agents.snapshot(agent) for agent in pilot_agents.list_all()]
    return {
        "ok": True,
        "count": len(agents),
        "agents": agents,
    }


@mcp.tool()
async def close_pilot_agent(agent_id: str) -> dict:
    """Close an idle helix-pilot agent and keep its last known result."""
    agent = pilot_agents.get(agent_id)
    if not agent:
        return {"ok": False, "error": f"Unknown agent_id: {agent_id}"}
    try:
        pilot_agents.close(agent)
    except ValueError as e:
        return {"ok": False, "error": str(e), "agent_id": agent_id}
    return pilot_agents.snapshot(agent)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
