"""Tests for ScreenCache — screenshot deduplication logic."""

import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from helix_pilot import PilotConfig, ScreenCache


def _make_cache() -> ScreenCache:
    """Create a ScreenCache with mocked CoreOperations."""
    config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))
    ops = MagicMock()
    return ScreenCache(config, ops)


class TestScreenCache(unittest.TestCase):
    """ScreenCache tracks screenshot descriptions to avoid redundant LLM calls."""

    def test_initial_state_no_cached_description(self):
        cache = _make_cache()
        self.assertIsNone(cache._last_description)
        self.assertEqual(cache._last_time, 0)

    def test_invalidate_resets_time(self):
        cache = _make_cache()
        cache._last_time = time.time()
        cache.invalidate()
        self.assertEqual(cache._last_time, 0)

    def test_cache_ttl_configured(self):
        cache = _make_cache()
        self.assertGreater(cache._cache_ttl, 0)

    def test_diff_threshold_configured(self):
        cache = _make_cache()
        self.assertGreater(cache._diff_threshold, 0)
        self.assertLess(cache._diff_threshold, 1.0)


if __name__ == "__main__":
    unittest.main()
