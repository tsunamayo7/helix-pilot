"""Tests for SafetyGuard — window validation, text input safety."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from helix_pilot import PilotConfig, PilotLogger, SafetyGuard


def _make_guard(**overrides) -> SafetyGuard:
    """Create a SafetyGuard with a mock logger."""
    config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))
    config._data.update(overrides)
    logger = MagicMock(spec=PilotLogger)
    return SafetyGuard(config, logger)


class TestWindowValidation(unittest.TestCase):
    """SafetyGuard.validate_window checks."""

    def test_denied_window_blocked(self):
        guard = _make_guard(safe_mode=False)
        ok, reason = guard.validate_window("Task Manager")
        self.assertFalse(ok)
        self.assertIn("denied", reason.lower())

    def test_denied_window_partial_match(self):
        guard = _make_guard(safe_mode=False)
        ok, _ = guard.validate_window("Windows Security Center")
        self.assertFalse(ok)

    def test_allowed_window_passes(self):
        guard = _make_guard(safe_mode=False)
        ok, reason = guard.validate_window("Google Chrome")
        self.assertTrue(ok)

    def test_safe_mode_requires_window(self):
        guard = _make_guard(safe_mode=True)
        ok, reason = guard.validate_window("")
        self.assertFalse(ok)
        self.assertIn("safe_mode", reason)

    def test_safe_mode_read_only_bypass(self):
        guard = _make_guard(safe_mode=True)
        ok, reason = guard.validate_window("", action="screenshot")
        self.assertTrue(ok)
        self.assertIn("read-only", reason)

    def test_safe_mode_with_window_passes(self):
        guard = _make_guard(safe_mode=True)
        ok, _ = guard.validate_window("Notepad")
        self.assertTrue(ok)

    def test_empty_window_no_safe_mode_passes(self):
        guard = _make_guard(safe_mode=False)
        ok, _ = guard.validate_window("")
        self.assertTrue(ok)

    def test_administrator_window_blocked(self):
        guard = _make_guard(safe_mode=False)
        ok, _ = guard.validate_window("Administrator: Command Prompt")
        self.assertFalse(ok)

    def test_password_window_blocked(self):
        guard = _make_guard(safe_mode=False)
        ok, _ = guard.validate_window("Enter Password")
        self.assertFalse(ok)


class TestTextInputValidation(unittest.TestCase):
    """SafetyGuard.validate_text_input checks."""

    def test_password_pattern_blocked(self):
        guard = _make_guard()
        ok, reason = guard.validate_text_input("my password is abc123")
        self.assertFalse(ok)
        self.assertIn("denied", reason.lower())

    def test_api_key_pattern_blocked(self):
        guard = _make_guard()
        ok, _ = guard.validate_text_input("use this api_key to connect")
        self.assertFalse(ok)

    def test_normal_text_allowed(self):
        guard = _make_guard()
        ok, reason = guard.validate_text_input("Hello, world!")
        self.assertTrue(ok)


class TestReadOnlyActionBypass(unittest.TestCase):
    """Read-only actions bypass safe_mode window requirement."""

    READ_ONLY = ["screenshot", "describe", "find", "verify",
                 "list-windows", "status", "wait-stable", "resize", "record"]

    def test_all_read_only_actions_bypass_safe_mode(self):
        guard = _make_guard(safe_mode=True)
        for action in self.READ_ONLY:
            ok, reason = guard.validate_window("", action=action)
            self.assertTrue(ok, f"{action} should bypass safe_mode, got: {reason}")

    def test_mutating_action_blocked_without_window(self):
        guard = _make_guard(safe_mode=True)
        for action in ["click", "type", "hotkey"]:
            ok, _ = guard.validate_window("", action=action)
            self.assertFalse(ok, f"{action} should be blocked without window")


if __name__ == "__main__":
    unittest.main()
