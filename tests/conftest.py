"""Shared test configuration — ensure scripts/ is importable."""

import sys
from pathlib import Path

# Add scripts/ to sys.path so `import helix_pilot` works in tests.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
