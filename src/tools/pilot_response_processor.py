"""Pilot response parsing and execution helpers."""

import json
import logging
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

PILOT_PATTERN = re.compile(r"<<PILOT:(\w[\w-]*)((?::\w[\w-]*=[^:>]*)*)\s*>>")
CODE_BLOCK_PATTERN = re.compile(
    r"```(?P<lang>[A-Za-z0-9_+-]*)[ \t]*\r?\n?(?P<body>.*?)```",
    re.DOTALL,
)


def get_system_prompt_addition(screen_context: str = "", lang: str = "ja") -> str:
    """Return the Helix Pilot system prompt addition."""
    if lang == "ja":
        prompt = (
            "\n\n【Helix Pilot - GUI自動操作】\n"
            "正規インターフェースは JSON Action Schema です。\n"
            "推奨出力は ```json ... ``` の fenced JSON を 1 個だけ、余計な解説なしです。\n"
            "生 JSON 1 個だけの出力も受理されます。\n"
            "例:\n"
            "```json\n"
            "{\"action\":\"status\",\"args\":{},\"mode\":\"draft_only\",\"context\":{\"site_policy\":\"helix_internal\"}}\n"
            "```\n"
            "従来の <<PILOT:...>> は後方互換としてのみ利用可能です。\n"
            "JSON を使えない場合のみ legacy marker を使ってください。\n"
            "利用可能アクションの例: list-windows, auto, browse, click, type, hotkey,\n"
            "scroll, find, describe, verify, screenshot, wait-stable。\n"
            "legacy 例:\n"
            "<<PILOT:status>>\n"
        )
    else:
        prompt = (
            "\n\n[Helix Pilot - GUI Automation]\n"
            "The canonical interface is JSON Action Schema.\n"
            "Preferred output is exactly one fenced JSON block with no extra commentary.\n"
            "A single raw JSON object is also accepted.\n"
            "Example:\n"
            "```json\n"
            "{\"action\":\"status\",\"args\":{},\"mode\":\"draft_only\",\"context\":{\"site_policy\":\"helix_internal\"}}\n"
            "```\n"
            "Legacy <<PILOT:...>> markers remain supported only for backward compatibility.\n"
            "Use legacy markers only if JSON Action Schema cannot be emitted.\n"
            "Available actions include list-windows, auto, browse, click, type, hotkey,\n"
            "scroll, find, describe, verify, screenshot, and wait-stable.\n"
            "Legacy example:\n"
            "<<PILOT:status>>\n"
        )

    if screen_context:
        if lang == "ja":
            prompt += f"\n【現在の画面状態】\n{screen_context}\n"
        else:
            prompt += f"\n[Current Screen State]\n{screen_context}\n"

    return prompt


def parse_pilot_calls(response: str) -> List[Dict[str, Any]]:
    """Parse legacy <<PILOT:...>> markers from a response."""
    calls: List[Dict[str, Any]] = []
    for match in PILOT_PATTERN.finditer(response):
        command = match.group(1)
        params_str = match.group(2)
        params: Dict[str, str] = {}
        if params_str:
            for segment in params_str.lstrip(":").split(":"):
                if "=" in segment:
                    key, value = segment.split("=", 1)
                    params[key.strip()] = value.strip()
        calls.append({
            "command": command,
            "params": params,
            "match": match.group(0),
        })
    return calls


def _build_json_action_call(payload: Any, match: str) -> Dict[str, Any] | None:
    """Normalize an Action Schema payload into the internal call format."""
    if not isinstance(payload, dict):
        return None
    action = payload.get("action")
    if not isinstance(action, str) or not action.strip():
        return None
    return {
        "request": payload,
        "match": match,
        "action": action.strip(),
    }


def _parse_full_json_object(text: str) -> Dict[str, Any] | None:
    """Parse only when the full trimmed response is a single JSON object."""
    stripped = text.strip()
    if not stripped or not stripped.startswith("{"):
        return None
    try:
        decoder = json.JSONDecoder()
        payload, end = decoder.raw_decode(stripped)
    except Exception:
        return None
    if stripped[end:].strip():
        return None
    return _build_json_action_call(payload, text)


def parse_json_action_calls(response: str) -> List[Dict[str, Any]]:
    """Extract JSON Action Schema calls from fenced or raw JSON responses."""
    calls: List[Dict[str, Any]] = []

    for match in CODE_BLOCK_PATTERN.finditer(response):
        raw = match.group("body").strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        call = _build_json_action_call(payload, match.group(0))
        if call:
            calls.append(call)

    if calls:
        return calls

    raw_call = _parse_full_json_object(response)
    if raw_call:
        calls.append(raw_call)

    return calls


def execute_and_replace(
    response: str,
    pilot_tool,
    max_iterations: int = 3,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Execute Pilot calls inside a response and replace them with results."""
    executed: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        json_calls = parse_json_action_calls(response)
        marker_calls = parse_pilot_calls(response)
        if not json_calls and not marker_calls:
            break

        for call in json_calls:
            request = call["request"]
            action = call["action"]
            if hasattr(pilot_tool, "execute_json"):
                result = pilot_tool.execute_json(request)
            else:
                result = pilot_tool.execute(action, request.get("args", {}))

            ok = result.get("ok", False)
            result_text = result.get("result", result.get("error", ""))
            executed.append({
                "command": action,
                "params": request.get("args", {}),
                "ok": ok,
                "result": str(result_text)[:500],
            })

            if ok:
                replacement = f"\n\n[Pilot JSON: {action}] {str(result_text)[:500]}\n"
            else:
                err = result.get("error", {})
                if isinstance(err, dict):
                    err_msg = err.get("message", "unknown")
                else:
                    err_msg = str(err)
                replacement = f"\n\n[Pilot JSON: {action} ERROR] {err_msg}\n"
            response = response.replace(call["match"], replacement, 1)

        for call in marker_calls:
            command = call["command"]
            params = call["params"]
            result = pilot_tool.execute(command, params)
            executed.append({
                "command": command,
                "params": params,
                "ok": result.get("ok", False),
                "result": str(result.get("result", result.get("error", "")))[:500],
            })

            if result.get("ok", False):
                replacement = f"\n\n[Pilot: {command}] {str(result.get('result', ''))[:500]}\n"
            else:
                replacement = f"\n\n[Pilot: {command} ERROR] {result.get('error', 'unknown')}\n"
            response = response.replace(call["match"], replacement, 1)

    return response, executed
