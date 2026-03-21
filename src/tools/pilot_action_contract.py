"""
Helix Pilot v13 action contract / policy helpers.

This module is GUI-framework agnostic so it can be reused from:
- scripts/helix_pilot.py (CLI runtime)
- src/tools/helix_pilot_tool.py (embedded runtime)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple
import re
import uuid


READ_ONLY_ACTIONS: Set[str] = {
    "status",
    "list-windows",
    "screenshot",
    "describe",
    "verify",
    "find",
    "wait-stable",
    "resize",
    "record",
}

MUTATING_ACTIONS: Set[str] = {
    "click",
    "click-screenshot",
    "type",
    "hotkey",
    "scroll",
    "auto",
    "browse",
    "attach",
    "run-scenario",
    "submit",
    "publish",
}

FINAL_ACTIONS: Set[str] = {
    "submit",
    "publish",
    "final-submit",
}

VALID_MODES: Set[str] = {
    "observe_only",
    "draft_only",
    "apply_with_approval",
    "publish_human_final",
}


DEFAULT_SITE_POLICIES: Dict[str, Dict[str, Any]] = {
    # Default for internal Helix usage.
    "helix_internal": {
        "allowed_actions": sorted(READ_ONLY_ACTIONS | MUTATING_ACTIONS),
        "denied_actions": sorted(FINAL_ACTIONS),
        "require_approval_actions": [],
        "block_final_submit": True,
    },
    "browser_general_observe": {
        "allowed_actions": sorted(READ_ONLY_ACTIONS),
        "denied_actions": sorted(MUTATING_ACTIONS),
        "require_approval_actions": [],
        "block_final_submit": True,
    },
    "github_release_draft": {
        "allowed_actions": sorted((READ_ONLY_ACTIONS | MUTATING_ACTIONS) - FINAL_ACTIONS),
        "denied_actions": sorted(FINAL_ACTIONS),
        "require_approval_actions": ["browse"],
        "block_final_submit": True,
    },
    "x_draft_only": {
        "allowed_actions": sorted((READ_ONLY_ACTIONS | MUTATING_ACTIONS) - FINAL_ACTIONS),
        "denied_actions": sorted(FINAL_ACTIONS),
        "require_approval_actions": ["browse", "type", "hotkey"],
        "block_final_submit": True,
    },
    "reddit_draft_only": {
        "allowed_actions": sorted((READ_ONLY_ACTIONS | MUTATING_ACTIONS) - FINAL_ACTIONS),
        "denied_actions": sorted(FINAL_ACTIONS),
        "require_approval_actions": ["browse", "type"],
        "block_final_submit": True,
    },
    "hn_draft_only": {
        "allowed_actions": sorted((READ_ONLY_ACTIONS | MUTATING_ACTIONS) - FINAL_ACTIONS),
        "denied_actions": sorted(FINAL_ACTIONS),
        "require_approval_actions": ["browse", "type"],
        "block_final_submit": True,
    },
}


DEFAULT_IMMUTABLE_POLICY: Dict[str, Any] = {
    "blocked_paths": [
        ".env",
        "secrets/",
    ],
    "blocked_text_patterns": [
        r"sk-[A-Za-z0-9]{20,}",
        r"ghp_[A-Za-z0-9]{20,}",
        r"AIza[0-9A-Za-z\-_]{20,}",
    ],
    "blocked_actions": ["submit", "publish", "final-submit"],
    "block_final_submit": True,
}


def build_action_request(
    action: str,
    args: Optional[Dict[str, Any]] = None,
    mode: str = "draft_only",
    context: Optional[Dict[str, Any]] = None,
    request_id: str = "",
) -> Dict[str, Any]:
    if not request_id:
        request_id = str(uuid.uuid4())
    return {
        "request_id": request_id,
        "mode": mode if mode in VALID_MODES else "draft_only",
        "action": str(action or "").strip(),
        "args": dict(args or {}),
        "context": dict(context or {}),
    }


def normalize_action_request(
    payload: Dict[str, Any],
    default_mode: str = "draft_only",
    default_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("action request must be a JSON object")
    action = str(payload.get("action", "")).strip()
    if not action:
        raise ValueError("action is required")
    request_id = str(payload.get("request_id", "")).strip() or str(uuid.uuid4())
    mode = str(payload.get("mode", default_mode)).strip()
    if mode not in VALID_MODES:
        mode = default_mode if default_mode in VALID_MODES else "draft_only"
    args = payload.get("args", {})
    if not isinstance(args, dict):
        raise ValueError("args must be an object")
    context = payload.get("context", {})
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    merged_context = dict(default_context or {})
    merged_context.update(context)
    return {
        "request_id": request_id,
        "mode": mode,
        "action": action,
        "args": args,
        "context": merged_context,
    }


def is_read_only_action(action: str) -> bool:
    return action in READ_ONLY_ACTIONS


def is_mutating_action(action: str) -> bool:
    return action in MUTATING_ACTIONS


def classify_action(action: str) -> str:
    if is_read_only_action(action):
        return "read_only"
    if is_mutating_action(action):
        return "mutating"
    return "unknown"


def required_scopes_for_action(
    action: str,
    args: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    project_root: Optional[Path] = None,
) -> Set[str]:
    args = args or {}
    context = context or {}
    scopes: Set[str] = set()

    if action in READ_ONLY_ACTIONS:
        scopes.add("FS_READ")

    if action in {"click", "click-screenshot", "type", "hotkey", "scroll"}:
        scopes.add("FS_WRITE")

    if action in {"auto", "run-scenario"}:
        scopes.update({"FS_WRITE", "BULK_EDIT"})

    if action in {"browse", "publish", "submit"}:
        scopes.update({"NETWORK", "FS_WRITE"})

    if action in {"attach"}:
        scopes.add("FS_READ")
        path_value = str(args.get("path", "")).strip()
        if path_value and project_root:
            try:
                p = Path(path_value)
                if not p.is_absolute():
                    p = (project_root / p)
                p = p.resolve()
                p.relative_to(project_root.resolve())
            except Exception:
                scopes.add("OUTSIDE_PROJECT")

    caller = str(context.get("caller", "")).lower()
    if caller in {"web", "external"} and action in {"auto", "browse"}:
        scopes.add("NETWORK")

    return scopes


def map_error_code(error_type: str = "", error_message: str = "", action: str = "") -> str:
    et = (error_type or "").lower()
    em = (error_message or "").lower()
    action = (action or "").lower()

    if "policy" in et or "policy" in em:
        return "policy_blocked"
    if "permission" in et or "permission" in em:
        return "permission_denied"
    if "window" in et or "window not found" in em:
        return "window_not_found"
    if "focus" in et or "focus" in em:
        return "focus_mismatch"
    if "timeout" in et or "timeout" in em:
        return "timeout"
    if "idle" in em or "user activity" in em or "busy" in em:
        return "user_busy"
    if "vision" in et or "ollama" in em:
        return "vision_unavailable"
    if "model" in et or "model" in em:
        return "model_unavailable"
    if action in {"submit", "publish"} and ("blocked" in em or "denied" in em):
        return "policy_blocked"
    if "not available" in em or "unknown action" in em or "unsupported" in em:
        return "not_available"
    return "execution_failed"


def _find_text_risk(text: str, patterns: Iterable[str]) -> Optional[str]:
    for pat in patterns:
        try:
            if re.search(pat, text, flags=re.IGNORECASE):
                return pat
        except re.error:
            # Treat malformed regex as a plain substring.
            if pat.lower() in text.lower():
                return pat
    return None


def evaluate_action_policy(
    request: Dict[str, Any],
    site_policies: Optional[Dict[str, Dict[str, Any]]] = None,
    immutable_policy: Optional[Dict[str, Any]] = None,
    project_root: Optional[Path] = None,
    approval_checker: Optional[Callable[[Set[str]], Tuple[bool, str]]] = None,
) -> Tuple[bool, str, str, list[str], Set[str]]:
    """
    Returns:
      (allowed, error_code, error_message, warnings, required_scopes)
    """
    warnings: list[str] = []
    action = request.get("action", "")
    mode = request.get("mode", "draft_only")
    args = request.get("args", {}) or {}
    context = request.get("context", {}) or {}
    site_policy_name = str(context.get("site_policy", "")).strip() or "helix_internal"

    req_scopes = required_scopes_for_action(action, args, context, project_root)
    policy_map = dict(DEFAULT_SITE_POLICIES)
    policy_map.update(site_policies or {})
    imm = dict(DEFAULT_IMMUTABLE_POLICY)
    imm.update(immutable_policy or {})

    action_class = classify_action(action)
    if action_class == "unknown":
        return False, "not_available", f"Unknown action: {action}", warnings, req_scopes

    # Mode gating
    if mode == "observe_only" and action_class == "mutating":
        return False, "policy_blocked", f"Action '{action}' is blocked in observe_only mode", warnings, req_scopes

    if mode in {"draft_only", "publish_human_final"}:
        if action in FINAL_ACTIONS:
            return False, "policy_blocked", "Final submit/publish is blocked by mode", warnings, req_scopes

    # Site policy gating
    site_policy = policy_map.get(site_policy_name)
    if not site_policy:
        warnings.append(f"Unknown site_policy '{site_policy_name}', fallback to helix_internal")
        site_policy = policy_map["helix_internal"]
    allowed_actions = set(site_policy.get("allowed_actions", []))
    denied_actions = set(site_policy.get("denied_actions", []))
    if allowed_actions and action not in allowed_actions:
        return False, "policy_blocked", f"Action '{action}' not allowed by site_policy '{site_policy_name}'", warnings, req_scopes
    if action in denied_actions:
        return False, "policy_blocked", f"Action '{action}' denied by site_policy '{site_policy_name}'", warnings, req_scopes

    if site_policy.get("block_final_submit", False) and action in FINAL_ACTIONS:
        return False, "policy_blocked", "Final submit/publish blocked by site_policy", warnings, req_scopes

    # Immutable policy gating
    blocked_actions = set(imm.get("blocked_actions", []))
    if action in blocked_actions:
        return False, "policy_blocked", f"Action '{action}' blocked by immutable_policy", warnings, req_scopes
    if imm.get("block_final_submit", True) and action in FINAL_ACTIONS:
        return False, "policy_blocked", "Final submit/publish blocked by immutable_policy", warnings, req_scopes

    text_candidate = str(args.get("text", "") or args.get("instruction", "") or "")
    pat = _find_text_risk(text_candidate, imm.get("blocked_text_patterns", []))
    if pat:
        return False, "policy_blocked", f"Input blocked by immutable_policy pattern: {pat}", warnings, req_scopes

    path_candidate = str(args.get("path", "")).strip()
    if path_candidate:
        for blocked_prefix in imm.get("blocked_paths", []):
            blocked_prefix = str(blocked_prefix).strip()
            if blocked_prefix and blocked_prefix.lower() in path_candidate.lower():
                return False, "policy_blocked", f"Path blocked by immutable_policy: {blocked_prefix}", warnings, req_scopes

    # Approval gate (mutating + apply_with_approval + explicit required-by-site)
    requires_approval = mode == "apply_with_approval" and action_class == "mutating"
    requires_approval = requires_approval or (
        action in set(site_policy.get("require_approval_actions", []))
    )
    if requires_approval and approval_checker:
        ok, msg = approval_checker(req_scopes)
        if not ok:
            return False, "permission_denied", msg or "approval required", warnings, req_scopes

    return True, "", "", warnings, req_scopes

