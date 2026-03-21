"""
Helix Pilot Tool — アプリ内統合用シングルトンラッパー

scripts/helix_pilot.py の HelixPilot クラスをラップし、
デスクトップ GUI タブ（cloudAI / localAI / mixAI）から呼び出し可能にする。

使用パターン:
    tool = HelixPilotTool.get_instance()
    if tool.is_available:
        result = tool.execute("describe", {"window": "Helix AI Studio"})
"""

import os
import sys
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# アプリルートパス
_APP_ROOT = Path(__file__).parent.parent.parent

try:
    from .pilot_action_contract import build_action_request
except Exception:
    def build_action_request(action: str, args: dict | None = None, mode: str = "draft_only",
                             context: dict | None = None, request_id: str = "") -> dict:
        return {
            "request_id": request_id or str(uuid.uuid4()),
            "mode": mode,
            "action": action,
            "args": args or {},
            "context": context or {},
        }


class HelixPilotTool:
    """Helix Pilot シングルトンラッパー"""

    _instance: Optional["HelixPilotTool"] = None

    def __init__(self):
        self._pilot = None
        self._config_path = _APP_ROOT / "config" / "helix_pilot.json"
        self._available: Optional[bool] = None
        self._last_error: str = ""
        self._sandbox_bridge = None  # SandboxPilotBridge (sandbox モード用)
        self._mode: str = "host"     # "host" or "sandbox"

    @classmethod
    def get_instance(cls) -> "HelixPilotTool":
        """シングルトンインスタンスを取得"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_available(self) -> bool:
        """Pilot が利用可能か（Ollama接続 + Visionモデル存在）"""
        if self._available is not None:
            return self._available
        self._available = self._check_availability()
        return self._available

    @property
    def mode(self) -> str:
        """現在の動作モード ("host" or "sandbox")"""
        return self._mode

    def set_sandbox_bridge(self, bridge):
        """SandboxPilotBridge を設定/解除

        Args:
            bridge: SandboxPilotBridge インスタンス (None でホストモードに戻る)
        """
        self._sandbox_bridge = bridge
        if bridge and bridge.is_available:
            self._mode = "sandbox"
            logger.info("[HelixPilotTool] Switched to SANDBOX mode")
        else:
            self._mode = "host"
            self._sandbox_bridge = None
            logger.info("[HelixPilotTool] Switched to HOST mode")

    def reset_availability(self):
        """利用可能性キャッシュをリセット（設定変更後に呼ぶ）"""
        self._available = None
        self._pilot = None

    @property
    def last_error(self) -> str:
        """最後のエラーメッセージ"""
        return self._last_error

    def _check_availability(self) -> bool:
        """Ollama 接続 + Vision モデルの存在確認"""
        try:
            config = self._load_config()
            endpoint = config.get("ollama_endpoint", "http://localhost:11434")
            vision_model = config.get("vision_model", "")

            if not vision_model:
                self._last_error = "vision_not_set"
                return False

            # Ollama 接続確認
            import httpx
            try:
                resp = httpx.get(f"{endpoint}/api/tags", timeout=5.0)
                if resp.status_code != 200:
                    self._last_error = "ollama_not_connected"
                    return False
            except Exception:
                self._last_error = "ollama_not_connected"
                return False

            # Vision モデル存在確認
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            # 完全一致 or タグなし一致
            found = False
            for name in model_names:
                if name == vision_model or name.split(":")[0] == vision_model.split(":")[0]:
                    found = True
                    break

            if not found:
                self._last_error = f"vision_not_found:{vision_model}"
                return False

            self._last_error = ""
            return True

        except Exception as e:
            logger.warning(f"[HelixPilotTool] Availability check failed: {e}")
            self._last_error = "ollama_not_connected"
            return False

    def _load_config(self) -> dict:
        """config/helix_pilot.json を読み込み"""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"[HelixPilotTool] Config load error: {e}")
        return {}

    def _build_action_context(self) -> dict:
        config = self._load_config()
        return {
            "caller": "embedded_adapter",
            "site_policy": config.get("default_site_policy", "helix_internal"),
            "task_type": "embedded_gui_assist",
            "llm_family": "agnostic",
        }

    def _default_mode(self) -> str:
        config = self._load_config()
        return config.get("execution_mode", "draft_only")

    def _ensure_pilot(self):
        """HelixPilot インスタンスを lazy 初期化"""
        if self._pilot is not None:
            return

        # DPI 競合防止: PyQt6 が既に DPI Awareness を設定しているため
        os.environ["HELIX_PILOT_SKIP_DPI"] = "1"

        # scripts/ を sys.path に追加
        scripts_dir = str(_APP_ROOT / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        try:
            from helix_pilot import HelixPilot
            self._pilot = HelixPilot(
                config_path=self._config_path,
                output_mode="compact",
            )
            logger.info("[HelixPilotTool] HelixPilot initialized")
        except Exception as e:
            logger.error(f"[HelixPilotTool] HelixPilot init failed: {e}")
            raise

    def execute(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        コマンドを実行

        Args:
            command: コマンド名 (auto/browse/click/type/find/describe/verify/
                     screenshot/scroll/hotkey/wait-stable/status)
            params: コマンドパラメータ辞書

        Returns:
            dict: 実行結果 {"ok": bool, "result": ..., "error": ...}
        """
        action_request = build_action_request(
            action=command,
            args=params or {},
            mode=self._default_mode(),
            context=self._build_action_context(),
        )
        return self.execute_json(action_request)

    def execute_json(self, action_request: Dict[str, Any]) -> Dict[str, Any]:
        """v13 JSON Action Schema 実行エントリポイント。"""
        request_id = str(action_request.get("request_id", "")) or str(uuid.uuid4())
        action = str(action_request.get("action", "")).strip()
        mode = str(action_request.get("mode", self._default_mode()))
        args = action_request.get("args", {}) if isinstance(action_request.get("args", {}), dict) else {}

        # sandbox モード: bridge が有効なら sandbox 経由で操作
        if (self._mode == "sandbox"
                and self._sandbox_bridge is not None
                and self._sandbox_bridge.is_available):
            raw = self._execute_via_sandbox(action, args)
            if raw.get("ok", False) and "request_id" in raw and "action" in raw:
                return raw
            if raw.get("ok", False):
                return {
                    "ok": True,
                    "request_id": request_id,
                    "action": action,
                    "mode": mode,
                    "result": raw,
                    "warnings": [],
                    "evidence": {"mode": "sandbox"},
                }
            return {
                "ok": False,
                "request_id": request_id,
                "action": action,
                "mode": mode,
                "error": {
                    "code": "execution_failed",
                    "message": raw.get("error", "sandbox execution failed"),
                    "error_type": raw.get("error_type", ""),
                },
                "result": raw,
                "warnings": [],
                "evidence": {"mode": "sandbox"},
            }

        # ホストモード
        try:
            self._ensure_pilot()
        except Exception as e:
            return {
                "ok": False,
                "request_id": request_id,
                "action": action,
                "mode": mode,
                "error": {"code": "not_available", "message": f"Pilot init failed: {e}"},
                "warnings": [],
                "evidence": {},
            }

        try:
            if hasattr(self._pilot, "execute_json"):
                return self._pilot.execute_json(action_request)
        except Exception as e:
            logger.error(f"[HelixPilotTool] execute_json dispatch failed: {e}", exc_info=True)
            return {
                "ok": False,
                "request_id": request_id,
                "action": action,
                "mode": mode,
                "error": {"code": "execution_failed", "message": str(e), "error_type": type(e).__name__},
                "warnings": [],
                "evidence": {},
            }

        # legacy fallback
        return self._execute_on_host(action, args)

    def _execute_on_host(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """従来のホスト直接操作"""
        try:
            self._ensure_pilot()
        except Exception as e:
            return {"ok": False, "error": f"Pilot init failed: {e}"}

        try:
            window = params.get("window", "")
            result = None

            if command == "auto":
                result = self._pilot.cmd_auto(
                    instruction=params.get("instruction", ""),
                    window=window,
                    dry_run=params.get("dry_run", False),
                )
            elif command == "browse":
                result = self._pilot.cmd_browse(
                    instruction=params.get("instruction", ""),
                    window=window,
                    dry_run=params.get("dry_run", False),
                )
            elif command == "click":
                result = self._pilot.cmd_click(
                    x=int(params.get("x", 0)),
                    y=int(params.get("y", 0)),
                    window=window,
                )
            elif command == "type":
                result = self._pilot.cmd_type(
                    text=params.get("text", ""),
                    window=window,
                )
            elif command == "hotkey":
                result = self._pilot.cmd_hotkey(
                    keys=params.get("keys", ""),
                    window=window,
                )
            elif command == "scroll":
                result = self._pilot.cmd_scroll(
                    amount=int(params.get("amount", 0)),
                    window=window,
                )
            elif command == "find":
                result = self._pilot.cmd_find(
                    description=params.get("description", ""),
                    window=window,
                )
            elif command == "describe":
                result = self._pilot.cmd_describe(window=window)
            elif command == "verify":
                result = self._pilot.cmd_verify(
                    expected=params.get("expected", ""),
                    window=window,
                )
            elif command == "screenshot":
                result = self._pilot.cmd_screenshot(
                    window=window,
                    name=params.get("name", "pilot_shot"),
                )
            elif command == "wait-stable":
                result = self._pilot.cmd_wait_stable(
                    timeout=int(params.get("timeout", 30)),
                    window=window,
                )
            elif command == "status":
                result = self._pilot.cmd_status()
            elif command == "list-windows":
                if hasattr(self._pilot, "cmd_list_windows"):
                    result = self._pilot.cmd_list_windows()
                else:
                    s = self._pilot.cmd_status()
                    result = {
                        "ok": True,
                        "visible_windows": s.get("visible_windows", []),
                        "command": "list-windows",
                    }
            else:
                return {"ok": False, "error": f"Unknown command: {command}"}

            # HelixPilot の cmd_* は dict を返す
            if isinstance(result, dict):
                return result
            return {"ok": True, "result": str(result)}

        except Exception as e:
            logger.error(f"[HelixPilotTool] Execute error: {command} — {e}", exc_info=True)
            return {"ok": False, "error": str(e)}

    def _execute_via_sandbox(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """sandbox 経由で Pilot 操作を実行"""
        bridge = self._sandbox_bridge

        try:
            if command == "screenshot":
                data = bridge.screenshot()
                if data:
                    name = params.get("name", "sandbox_shot")
                    save_path = _APP_ROOT / "data" / "helix_pilot_screenshots" / f"{name}.png"
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_bytes(data)
                    from PIL import Image
                    img = Image.open(save_path)
                    return {
                        "ok": True,
                        "path": str(save_path),
                        "size": list(img.size),
                        "mode": "sandbox",
                        "command": "screenshot",
                    }
                return {"ok": False, "error": "Sandbox screenshot failed"}

            elif command == "click":
                return bridge.click(int(params.get("x", 0)), int(params.get("y", 0)))

            elif command == "type":
                return bridge.type_text(params.get("text", ""))

            elif command == "hotkey":
                return bridge.hotkey(params.get("keys", ""))

            elif command == "scroll":
                return bridge.scroll(int(params.get("amount", 0)))

            elif command == "describe":
                data = bridge.screenshot()
                if data:
                    return self._vision_from_bytes(data, "describe")
                return {"ok": False, "error": "Sandbox screenshot for describe failed"}

            elif command == "verify":
                data = bridge.screenshot()
                if data:
                    return self._vision_from_bytes(
                        data, "verify", expected=params.get("expected", ""))
                return {"ok": False, "error": "Sandbox screenshot for verify failed"}

            elif command == "find":
                data = bridge.screenshot()
                if data:
                    return self._vision_from_bytes(
                        data, "find", description=params.get("description", ""))
                return {"ok": False, "error": "Sandbox screenshot for find failed"}

            elif command == "wait-stable":
                timeout = int(params.get("timeout", 30))
                return self._wait_stable_sandbox(bridge, timeout)

            elif command == "status":
                return {
                    "ok": True,
                    "mode": "sandbox",
                    "backend": bridge.backend_type,
                    "available": bridge.is_available,
                }
            elif command == "list-windows":
                return {
                    "ok": False,
                    "error": "list-windows is not available in sandbox mode",
                    "error_type": "not_available",
                }

            else:
                return {"ok": False, "error": f"Unknown sandbox command: {command}"}

        except Exception as e:
            logger.error(f"[HelixPilotTool] Sandbox execute error: {command} -- {e}",
                         exc_info=True)
            return {"ok": False, "error": str(e)}

    def _vision_from_bytes(self, png_bytes: bytes, task: str, **kwargs) -> dict:
        """PNG バイト列をホスト側 Ollama Vision に送って解析

        Args:
            png_bytes: スクリーンショット PNG データ
            task: "describe" / "verify" / "find"
        """
        import base64
        try:
            config = self._load_config()
            endpoint = config.get("ollama_endpoint", "http://localhost:11434")
            vision_model = config.get("vision_model", "")

            if not vision_model:
                return {"ok": False, "error": "Vision model not configured"}

            b64 = base64.b64encode(png_bytes).decode()

            if task == "describe":
                prompt = (
                    "この画面のスクリーンショットを詳細に説明してください。"
                    "表示されているUI要素、テキスト、ボタン、入力フィールドなどを日本語で記述してください。"
                )
            elif task == "verify":
                expected = kwargs.get("expected", "")
                prompt = (
                    f"この画面が次の状態を満たしているか確認してください: 「{expected}」\n"
                    "結果を match: true/false で始め、理由を日本語で簡潔に説明してください。"
                )
            elif task == "find":
                description = kwargs.get("description", "")
                prompt = (
                    f"この画面から次のUI要素を探してください: 「{description}」\n"
                    "見つかった場合は x, y 座標 (ピクセル) を返してください。"
                    "形式: found: true, x: 数値, y: 数値"
                )
            else:
                return {"ok": False, "error": f"Unknown vision task: {task}"}

            import httpx
            resp = httpx.post(
                f"{endpoint}/api/generate",
                json={
                    "model": vision_model,
                    "prompt": prompt,
                    "images": [b64],
                    "stream": False,
                },
                timeout=60.0,
            )

            if resp.status_code == 200:
                result_text = resp.json().get("response", "")
                result = {"ok": True, "description": result_text, "mode": "sandbox"}

                # verify の場合は match フラグを抽出
                if task == "verify":
                    result["match"] = "match: true" in result_text.lower()

                # find の場合は座標を抽出
                if task == "find":
                    import re
                    x_match = re.search(r'x:\s*(\d+)', result_text)
                    y_match = re.search(r'y:\s*(\d+)', result_text)
                    if x_match and y_match:
                        result["found"] = True
                        result["x"] = int(x_match.group(1))
                        result["y"] = int(y_match.group(1))
                    else:
                        result["found"] = False

                return result
            else:
                return {"ok": False, "error": f"Ollama API error: {resp.status_code}"}

        except Exception as e:
            logger.error(f"[HelixPilotTool] Vision analysis failed: {e}")
            return {"ok": False, "error": str(e)}

    def _wait_stable_sandbox(self, bridge, timeout: int) -> dict:
        """sandbox 画面が安定するまで待機"""
        import time as _time
        prev = bridge.screenshot()
        for _ in range(timeout):
            _time.sleep(1)
            curr = bridge.screenshot()
            if prev == curr:
                return {"ok": True, "result": "Screen is stable", "mode": "sandbox"}
            prev = curr
        return {"ok": False, "error": "Screen did not stabilize"}

    def get_screen_context(self, window: str = "") -> str:
        """
        画面の describe 結果をテキストで返す（プロンプト注入用）

        Returns:
            str: 画面説明テキスト（失敗時は空文字）
        """
        try:
            self._ensure_pilot()
            result = self._pilot.cmd_describe(window=window)
            if isinstance(result, dict):
                if result.get("ok"):
                    return result.get("description", result.get("result", ""))
                else:
                    return f"[Screen context unavailable: {result.get('error', 'unknown')}]"
            return str(result)
        except Exception as e:
            logger.warning(f"[HelixPilotTool] Screen context error: {e}")
            return ""

    def shutdown(self):
        """アプリ終了時のクリーンアップ"""
        if self._pilot is not None:
            try:
                if hasattr(self._pilot, "shutdown"):
                    self._pilot.shutdown()
                logger.info("[HelixPilotTool] Shutdown completed")
            except Exception as e:
                logger.warning(f"[HelixPilotTool] Shutdown error: {e}")
            finally:
                self._pilot = None
