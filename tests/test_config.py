"""Tests for PilotConfig — configuration loading and validation."""

import json
import tempfile
import unittest
from pathlib import Path

from helix_pilot import PilotConfig


class TestPilotConfigDefaults(unittest.TestCase):
    """Verify that PilotConfig returns sane defaults without a config file."""

    def setUp(self):
        # Point to a non-existent file so defaults are used.
        self.config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))

    def test_ollama_endpoint_default(self):
        self.assertEqual(self.config.ollama_endpoint, "http://localhost:11434")

    def test_vision_model_default(self):
        self.assertIn("vision", self.config.vision_model)

    def test_safe_mode_defaults_to_true(self):
        self.assertTrue(self.config.safe_mode)

    def test_execution_mode_defaults_to_draft_only(self):
        self.assertEqual(self.config.execution_mode, "draft_only")

    def test_denied_windows_not_empty(self):
        self.assertGreater(len(self.config.denied_windows), 0)
        self.assertIn("Task Manager", self.config.denied_windows)

    def test_auto_config_has_required_keys(self):
        cfg = self.config.auto_cfg
        for key in ("max_steps", "step_timeout", "total_timeout"):
            self.assertIn(key, cfg)

    def test_browse_config_has_required_keys(self):
        cfg = self.config.browse_cfg
        self.assertIn("max_steps", cfg)
        self.assertIn("denied_domains", cfg)

    def test_action_safety_denied_hotkeys(self):
        safety = self.config.action_safety_cfg
        denied = safety["denied_hotkeys"]
        # Critical system shortcuts must always be blocked.
        self.assertIn("alt+f4", denied)
        self.assertIn("ctrl+alt+delete", denied)

    def test_immutable_policy_blocks_secrets(self):
        imm = self.config.immutable_policy
        self.assertGreater(len(imm["blocked_text_patterns"]), 0)

    def test_missing_attribute_raises(self):
        with self.assertRaises(AttributeError):
            _ = self.config.nonexistent_attr_xyz


class TestPilotConfigFileLoading(unittest.TestCase):
    """Verify config file overrides defaults correctly."""

    def test_custom_values_override_defaults(self):
        custom = {
            "ollama_endpoint": "http://myhost:9999",
            "vision_model": "gemma3:27b",
            "safe_mode": False,
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(custom, f)
            f.flush()
            config = PilotConfig(config_path=Path(f.name))

        self.assertEqual(config.ollama_endpoint, "http://myhost:9999")
        self.assertEqual(config.vision_model, "gemma3:27b")
        self.assertFalse(config.safe_mode)

    def test_partial_override_preserves_defaults(self):
        custom = {"vision_model": "moondream"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(custom, f)
            f.flush()
            config = PilotConfig(config_path=Path(f.name))

        self.assertEqual(config.vision_model, "moondream")
        # Other defaults should remain.
        self.assertEqual(config.ollama_endpoint, "http://localhost:11434")
        self.assertTrue(config.safe_mode)

    def test_invalid_json_falls_back_to_defaults(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("not valid json {{{")
            f.flush()
            config = PilotConfig(config_path=Path(f.name))

        # Should silently fall back to defaults.
        self.assertEqual(config.ollama_endpoint, "http://localhost:11434")

    def test_underscore_prefixed_keys_ignored(self):
        custom = {"_internal": "should be ignored", "safe_mode": False}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(custom, f)
            f.flush()
            config = PilotConfig(config_path=Path(f.name))

        self.assertFalse(config.safe_mode)
        with self.assertRaises(AttributeError):
            _ = config._internal


class TestPilotConfigProperties(unittest.TestCase):
    """Test computed properties."""

    def test_reasoning_model_fallback(self):
        config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))
        # When reasoning_model is empty, should fall back to vision_model.
        self.assertEqual(config.reasoning_model_name, config.vision_model)

    def test_reasoning_model_explicit(self):
        custom = {"reasoning_model": "qwen3.5:122b"}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(custom, f)
            f.flush()
            config = PilotConfig(config_path=Path(f.name))

        self.assertEqual(config.reasoning_model_name, "qwen3.5:122b")


if __name__ == "__main__":
    unittest.main()
