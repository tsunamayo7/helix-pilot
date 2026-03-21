import unittest
from pathlib import Path

from src.tools.pilot_action_contract import (
    build_action_request,
    normalize_action_request,
    evaluate_action_policy,
    required_scopes_for_action,
    map_error_code,
)


class TestPilotActionContract(unittest.TestCase):
    def test_build_and_normalize_action_request(self):
        req = build_action_request(
            action="click",
            args={"x": 1, "y": 2},
            mode="draft_only",
            context={"caller": "test"},
        )
        norm = normalize_action_request(req, default_mode="draft_only")
        self.assertEqual(norm["action"], "click")
        self.assertEqual(norm["args"]["x"], 1)
        self.assertEqual(norm["mode"], "draft_only")
        self.assertTrue(norm["request_id"])

    def test_observe_only_blocks_mutating(self):
        req = normalize_action_request({
            "action": "click",
            "mode": "observe_only",
            "args": {"x": 10, "y": 20},
            "context": {"site_policy": "helix_internal"},
        })
        ok, code, msg, _warnings, _scopes = evaluate_action_policy(req)
        self.assertFalse(ok)
        self.assertEqual(code, "policy_blocked")
        self.assertIn("observe_only", msg)

    def test_site_policy_blocks_final_submit(self):
        req = normalize_action_request({
            "action": "publish",
            "mode": "draft_only",
            "args": {},
            "context": {"site_policy": "x_draft_only"},
        })
        ok, code, _msg, _warnings, _scopes = evaluate_action_policy(req)
        self.assertFalse(ok)
        self.assertEqual(code, "policy_blocked")

    def test_immutable_policy_blocks_secret_like_text(self):
        req = normalize_action_request({
            "action": "type",
            "mode": "draft_only",
            "args": {"text": "token=sk-AAAAAAAAAAAAAAAAAAAAAAAAA"},
            "context": {"site_policy": "helix_internal"},
        })
        ok, code, _msg, _warnings, _scopes = evaluate_action_policy(req)
        self.assertFalse(ok)
        self.assertEqual(code, "policy_blocked")

    def test_apply_with_approval_uses_approval_checker(self):
        req = normalize_action_request({
            "action": "click",
            "mode": "apply_with_approval",
            "args": {"x": 1, "y": 2},
            "context": {"site_policy": "helix_internal"},
        })

        def deny(_scopes):
            return False, "approval required"

        ok, code, msg, _warnings, scopes = evaluate_action_policy(req, approval_checker=deny)
        self.assertFalse(ok)
        self.assertEqual(code, "permission_denied")
        self.assertIn("approval", msg)
        self.assertIn("FS_WRITE", scopes)

    def test_required_scopes_mapping(self):
        scopes = required_scopes_for_action("browse", args={}, context={"caller": "web"}, project_root=Path("."))
        self.assertIn("NETWORK", scopes)
        self.assertIn("FS_WRITE", scopes)

    def test_map_error_code(self):
        self.assertEqual(map_error_code("PilotWindowNotFoundError", "", "click"), "window_not_found")
        self.assertEqual(map_error_code("", "User activity detected", "type"), "user_busy")
        self.assertEqual(map_error_code("", "policy blocked", "publish"), "policy_blocked")


if __name__ == "__main__":
    unittest.main()

