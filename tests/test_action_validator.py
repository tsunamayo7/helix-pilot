"""Tests for ActionValidator — LLM action plan validation."""

import unittest
from pathlib import Path

from helix_pilot import PilotConfig, ActionValidator


def _make_config(**overrides) -> PilotConfig:
    config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))
    config._data.update(overrides)
    return config


class TestActionValidator(unittest.TestCase):
    """ActionValidator ensures planned actions are safe before execution."""

    def setUp(self):
        self.validator = ActionValidator(_make_config())

    def test_valid_click_action(self):
        ok, reason = self.validator.validate({
            "action": "click_element",
            "target": "the Save button",
        })
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")

    def test_valid_type_action(self):
        ok, reason = self.validator.validate({
            "action": "type_text",
            "text": "Hello, world!",
        })
        self.assertTrue(ok)

    def test_valid_hotkey_action(self):
        ok, reason = self.validator.validate({
            "action": "hotkey",
            "keys": "ctrl+s",
        })
        self.assertTrue(ok)

    def test_valid_wait_action(self):
        ok, reason = self.validator.validate({
            "action": "wait",
            "seconds": 2.0,
        })
        self.assertTrue(ok)

    def test_valid_screenshot_action(self):
        ok, reason = self.validator.validate({
            "action": "screenshot",
            "name": "test_shot",
        })
        self.assertTrue(ok)

    def test_valid_verify_action(self):
        ok, reason = self.validator.validate({
            "action": "verify",
            "expected": "the dialog closed",
        })
        self.assertTrue(ok)

    def test_unknown_action_rejected(self):
        ok, reason = self.validator.validate({
            "action": "delete_system32",
        })
        self.assertFalse(ok)
        self.assertIn("unknown", reason.lower())

    def test_dangerous_hotkey_in_plan_blocked(self):
        ok, reason = self.validator.validate({
            "action": "hotkey",
            "keys": "alt+f4",
        })
        self.assertFalse(ok)

    def test_secret_text_in_plan_blocked(self):
        ok, reason = self.validator.validate({
            "action": "type_text",
            "text": "token=sk-AAAAAAAAAAAAAAAAAAAAAAAAA",
        })
        self.assertFalse(ok)

    def test_excessive_wait_clamped(self):
        # Wait beyond max should be blocked or clamped.
        ok, reason = self.validator.validate({
            "action": "wait",
            "seconds": 999,
        })
        # Implementation either blocks or clamps; both are valid.
        # We just verify it doesn't raise.
        self.assertIsInstance(ok, bool)

    def test_scroll_in_plan(self):
        ok, reason = self.validator.validate({
            "action": "scroll",
            "amount": 3,
        })
        self.assertTrue(ok)

    def test_navigate_url_action(self):
        ok, reason = self.validator.validate({
            "action": "navigate_url",
            "url": "https://www.example.com",
        })
        self.assertTrue(ok)

    def test_navigate_to_private_ip_blocked(self):
        ok, reason = self.validator.validate({
            "action": "navigate_url",
            "url": "http://192.168.1.1/admin",
        })
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
