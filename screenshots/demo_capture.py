"""
helix-pilot デモGIF撮影スクリプト

helix-pilot のMCPツールを直接呼び出してデモ操作を実行し、
FFmpeg でデスクトップ録画→GIF変換する。

シーン:
  1. status → list_windows → screenshot → describe の一連の流れ
  2. auto でメモ帳を開いてテキスト入力
"""

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OUT_DIR = Path(__file__).parent / "demo"
FINAL_DIR = Path(__file__).parent.parent / "docs" / "demo"

# FFmpeg screen capture settings (Windows GDI grabber)
SCREEN_W, SCREEN_H = 3840, 2160
# Capture region: center portion for 1920x1080
CAP_W, CAP_H = 1920, 1080
CAP_X, CAP_Y = (SCREEN_W - CAP_W) // 2, (SCREEN_H - CAP_H) // 2


def start_recording(output_path: Path, fps=15):
    """FFmpeg でデスクトップ録画を開始（バックグラウンド）"""
    cmd = [
        "ffmpeg", "-y",
        "-f", "gdigrab",
        "-framerate", str(fps),
        "-offset_x", str(CAP_X),
        "-offset_y", str(CAP_Y),
        "-video_size", f"{CAP_W}x{CAP_H}",
        "-i", "desktop",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
        str(output_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)  # 録画開始待ち
    return proc


def stop_recording(proc):
    """録画を停止"""
    try:
        proc.stdin.write(b"q")
        proc.stdin.flush()
        proc.wait(timeout=5)
    except Exception:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def mp4_to_gif(mp4_path: Path, gif_path: Path, fps=10, width=800, trim_start=0, max_dur=None):
    """MP4→GIF変換"""
    input_args = ["-y"]
    if trim_start > 0:
        input_args += ["-ss", str(trim_start)]
    input_args += ["-i", str(mp4_path)]
    if max_dur:
        input_args += ["-t", str(max_dur)]

    palette = mp4_path.parent / "palette.png"

    vf = f"fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=diff"
    subprocess.run(["ffmpeg"] + input_args + ["-vf", vf, str(palette)], capture_output=True)

    vf_gif = f"fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3"
    subprocess.run(["ffmpeg"] + input_args + ["-i", str(palette), "-lavfi", vf_gif, str(gif_path)], capture_output=True)

    palette.unlink(missing_ok=True)

    if gif_path.exists():
        size_kb = gif_path.stat().st_size / 1024
        print(f"  -> {gif_path.name} ({size_kb:.0f}KB)")
    else:
        print(f"  x GIF conversion failed: {gif_path.name}")


def call_pilot_tool(tool_name: str, args: dict = None):
    """helix-pilot のツールを直接呼び出す"""
    from src.pilot import create_pilot
    pilot = create_pilot()

    method = getattr(pilot, f"cmd_{tool_name}", None)
    if method is None:
        print(f"  Tool not found: {tool_name}")
        return None

    result = method(**(args or {}))
    return result


def scene_tool_showcase():
    """シーン1: ツール一覧デモ（status → list_windows → screenshot → describe）"""
    print("[1/2] ツール呼び出しデモ...")

    from src.pilot import create_pilot
    pilot = create_pilot()

    print("  status...")
    status = pilot.cmd_status()
    print(f"    Ollama: {status.get('ollama', {}).get('available')}")
    print(f"    Screen: {status.get('screen_size')}")

    print("  list_windows...")
    windows = pilot.cmd_list_windows()
    win_list = windows.get("windows", [])
    print(f"    Found {len(win_list)} windows")

    print("  screenshot...")
    shot = pilot.cmd_screenshot(name="demo_full")
    print(f"    Saved: {shot.get('path')}")

    print("  describe...")
    desc = pilot.cmd_describe()
    description = desc.get("description", "")[:200]
    print(f"    Description: {description}...")

    return status, windows, shot, desc


def scene_notepad_auto():
    """シーン2: メモ帳を自動操作"""
    print("[2/2] メモ帳自動操作デモ...")

    from src.pilot import create_pilot
    pilot = create_pilot()

    # Open Notepad
    import pyautogui
    subprocess.Popen(["notepad.exe"])
    time.sleep(2)

    print("  type_text...")
    pilot.cmd_type(text="Hello from helix-pilot!\nThis text was typed by an AI agent.", window="メモ帳")
    time.sleep(1)

    print("  screenshot...")
    pilot.cmd_screenshot(window="メモ帳", name="demo_notepad")
    time.sleep(1)

    # Close notepad without saving
    pilot.cmd_hotkey(keys="alt+F4", window="メモ帳")
    time.sleep(0.5)
    pilot.cmd_hotkey(keys="tab")  # Focus "Don't Save"
    time.sleep(0.3)
    pilot.cmd_hotkey(keys="enter")

    print("  -> Notepad demo complete")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT_DIR.mkdir(exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # Scene 1: Tool showcase (just run tools, capture terminal-style output)
    print("=== helix-pilot Demo Capture ===\n")

    status, windows, shot, desc = scene_tool_showcase()

    # Save demo output as JSON for README
    demo_output = {
        "status": status,
        "windows_count": len(windows.get("windows", [])),
        "screenshot": {"ok": shot.get("ok"), "path": shot.get("path")},
        "description_preview": desc.get("description", "")[:300],
    }
    with open(FINAL_DIR / "demo_output.json", "w", encoding="utf-8") as f:
        json.dump(demo_output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Demo output saved: {FINAL_DIR / 'demo_output.json'}")

    # Scene 2: Notepad automation with screen recording
    print("\nStarting screen recording for Notepad demo...")
    mp4_path = OUT_DIR / "notepad_demo.mp4"
    rec = start_recording(mp4_path)

    try:
        time.sleep(1)  # let recording stabilize
        scene_notepad_auto()
        time.sleep(2)  # extra frames
    finally:
        stop_recording(rec)

    if mp4_path.exists():
        gif_path = FINAL_DIR / "notepad_demo.gif"
        mp4_to_gif(mp4_path, gif_path, trim_start=1, max_dur=15)

    print(f"\n✅ All demo files saved to: {FINAL_DIR}")


if __name__ == "__main__":
    main()
