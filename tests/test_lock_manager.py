"""Tests for LockManager — process-level lock."""

import os
import tempfile
import unittest
from pathlib import Path

from helix_pilot import PilotConfig, LockManager


def _make_lock() -> LockManager:
    """Create a LockManager with a temp lock file."""
    config = PilotConfig(config_path=Path("/tmp/nonexistent.json"))
    tmp = tempfile.mktemp(suffix=".json")
    config._data["lock_file"] = tmp
    # Override the lock_file_path property
    lock = LockManager(config)
    lock._lock_path = Path(tmp)
    lock._lock_path.parent.mkdir(parents=True, exist_ok=True)
    return lock


class TestLockManager(unittest.TestCase):
    """LockManager prevents concurrent GUI operations."""

    def test_acquire_and_release(self):
        lock = _make_lock()
        acquired = lock.acquire("test_op", timeout=5)
        self.assertTrue(acquired)
        info = lock.is_locked()
        self.assertTrue(info.get("locked"))
        lock.release()
        info = lock.is_locked()
        self.assertFalse(info.get("locked"))

    def test_double_acquire_by_same_process_blocked(self):
        # Same PID is alive, so second acquire should fail.
        lock = _make_lock()
        lock.acquire("op1", timeout=2)
        acquired = lock.acquire("op2", timeout=2)
        # Same process PID is alive, lock should not be granted.
        self.assertFalse(acquired)
        lock.release()

    def test_release_without_acquire(self):
        lock = _make_lock()
        # Should not raise.
        lock.release()

    def test_lock_contains_pid(self):
        lock = _make_lock()
        lock.acquire("test_op", timeout=5)
        info = lock.is_locked()
        self.assertEqual(info["pid"], os.getpid())
        self.assertEqual(info["operation"], "test_op")
        lock.release()


if __name__ == "__main__":
    unittest.main()
