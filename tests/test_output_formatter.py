"""Tests for OutputFormatter — JSON output formatting and compact mode."""

import unittest
from pathlib import Path

from helix_pilot import PilotConfig, OutputFormatter


def _make_config(**overrides) -> PilotConfig:
    config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))
    config._data.update(overrides)
    return config


class TestOutputFormatterNormal(unittest.TestCase):
    """Normal mode preserves all fields."""

    def setUp(self):
        self.formatter = OutputFormatter(_make_config(), mode="normal")

    def test_format_preserves_all_fields(self):
        payload = {"ok": True, "command": "status", "data": "hello"}
        result = self.formatter.format(payload)
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"], "status")
        self.assertEqual(result["data"], "hello")

    def test_format_returns_dict(self):
        result = self.formatter.format({"ok": True})
        self.assertIsInstance(result, dict)

    def test_normal_mode_keeps_timestamp(self):
        payload = {"ok": True, "timestamp": "2026-03-28T00:00:00"}
        result = self.formatter.format(payload)
        self.assertIn("timestamp", result)


class TestOutputFormatterCompact(unittest.TestCase):
    """Compact mode strips unnecessary fields for token efficiency."""

    def setUp(self):
        self.formatter = OutputFormatter(_make_config(), mode="compact")

    def test_compact_excludes_configured_fields(self):
        payload = {
            "ok": True,
            "command": "screenshot",
            "screenshot_path": "/tmp/shot.png",
            "timestamp": "2026-03-28T00:00:00",
            "vision_model": "gemma3:27b",
            "size": [1920, 1080],
        }
        result = self.formatter.format(payload)
        self.assertNotIn("screenshot_path", result)
        self.assertNotIn("timestamp", result)
        self.assertNotIn("vision_model", result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["command"], "screenshot")

    def test_compact_truncates_long_descriptions(self):
        long_desc = "x" * 1000
        payload = {"ok": True, "description": long_desc}
        result = self.formatter.format(payload)
        # Default max is 500 + "..."
        self.assertLessEqual(len(result["description"]), 503)
        self.assertTrue(result["description"].endswith("..."))

    def test_compact_preserves_short_descriptions(self):
        payload = {"ok": True, "description": "Short text"}
        result = self.formatter.format(payload)
        self.assertEqual(result["description"], "Short text")


class TestOutputFormatterMinimal(unittest.TestCase):
    """Minimal mode returns only essential fields."""

    def setUp(self):
        self.formatter = OutputFormatter(_make_config(), mode="minimal")

    def test_minimal_success(self):
        payload = {"ok": True, "command": "click", "extra": "data"}
        result = self.formatter.format(payload)
        self.assertTrue(result["ok"])
        self.assertNotIn("extra", result)

    def test_minimal_error(self):
        payload = {"ok": False, "error": "window not found", "command": "click"}
        result = self.formatter.format(payload)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "window not found")

    def test_minimal_find_found(self):
        payload = {"ok": True, "command": "find", "found": True, "x": 100, "y": 200}
        result = self.formatter.format(payload)
        self.assertTrue(result["found"])
        self.assertEqual(result["x"], 100)
        self.assertEqual(result["y"], 200)

    def test_minimal_find_not_found(self):
        payload = {"ok": True, "command": "find", "found": False}
        result = self.formatter.format(payload)
        self.assertFalse(result["found"])

    def test_minimal_verify(self):
        payload = {"ok": True, "command": "verify", "success": True}
        result = self.formatter.format(payload)
        self.assertTrue(result["success"])

    def test_minimal_auto(self):
        payload = {
            "ok": True, "command": "auto",
            "steps_succeeded": 5, "steps_executed": 6,
            "errors": ["step 3 failed"],
        }
        result = self.formatter.format(payload)
        self.assertEqual(result["steps_succeeded"], 5)
        self.assertEqual(result["steps_executed"], 6)
        self.assertIn("step 3 failed", result["errors"])


if __name__ == "__main__":
    unittest.main()
