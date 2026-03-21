"""helix-pilot core — thin wrapper around scripts/helix_pilot.py."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

# Make scripts/ importable so we can reuse HelixPilot directly
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from helix_pilot import HelixPilot, PilotConfig  # noqa: E402


def create_pilot(
    config_path: Optional[Path] = None,
    output_mode: str = "compact",
) -> HelixPilot:
    """Create a HelixPilot instance with sensible defaults for MCP usage.

    Args:
        config_path: Path to helix_pilot.json config.
                     None = auto-detect from project root.
        output_mode: Output verbosity — "compact" (default) or "normal".

    Returns:
        Configured HelixPilot instance.
    """
    return HelixPilot(config_path=config_path, output_mode=output_mode)


__all__ = ["HelixPilot", "PilotConfig", "create_pilot"]
