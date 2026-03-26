"""
ターミナル風デモGIFを生成するスクリプト

helix-pilot のMCPツール呼び出しをターミナル風にレンダリングし、
タイピングアニメーション付きのGIFを生成する。
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent.parent / "docs" / "demo"

# Terminal colors (dark theme)
BG = (30, 30, 46)
FG = (205, 214, 244)
GREEN = (166, 227, 161)
BLUE = (137, 180, 250)
YELLOW = (249, 226, 175)
PURPLE = (203, 166, 247)
CYAN = (148, 226, 213)
RED = (243, 139, 168)
GRAY = (108, 112, 134)

W, H = 900, 560
MARGIN = 20
LINE_H = 22
FONT_SIZE = 16


def get_font(size=FONT_SIZE):
    """等幅フォントを取得"""
    font_paths = [
        "C:/Windows/Fonts/consola.ttf",  # Consolas
        "C:/Windows/Fonts/cour.ttf",     # Courier New
    ]
    for p in font_paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_frame(lines, font):
    """ターミナルフレームを描画"""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([(0, 0), (W, 32)], fill=(49, 50, 68))
    draw.ellipse([(10, 10), (22, 22)], fill=RED)
    draw.ellipse([(28, 10), (40, 22)], fill=YELLOW)
    draw.ellipse([(46, 10), (58, 22)], fill=GREEN)
    title_font = get_font(13)
    draw.text((W // 2 - 80, 8), "helix-pilot — MCP Demo", fill=GRAY, font=title_font)

    y = 40
    for line_parts in lines:
        x = MARGIN
        for text, color in line_parts:
            draw.text((x, y), text, fill=color, font=font)
            bbox = font.getbbox(text)
            x += bbox[2] - bbox[0]
        y += LINE_H
        if y > H - 10:
            break

    return img


def create_demo_gif():
    """MCP ツール呼び出しデモの GIF を作成"""
    font = get_font()

    # Define terminal content progressively
    scenes = [
        # Scene 1: Prompt
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
        ],
        # Scene 2: status call
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.status()", PURPLE)],
        ],
        # Scene 3: status result
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.status()", PURPLE)],
            [("  ✓ ", GREEN), ("Ollama: ", FG), ("connected", GREEN), ("  (mistral-small3.2)", GRAY)],
            [("  ✓ ", GREEN), ("Screen: ", FG), ("3840×2160", CYAN)],
            [("  ✓ ", GREEN), ("Windows: ", FG), ("22 visible", CYAN)],
            [("  ✓ ", GREEN), ("Safe mode: ", FG), ("ON", GREEN)],
        ],
        # Scene 4: screenshot call
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.status()", PURPLE)],
            [("  ✓ ", GREEN), ("Ollama: ", FG), ("connected", GREEN), ("  (mistral-small3.2)", GRAY)],
            [("  ✓ ", GREEN), ("Screen: ", FG), ("3840×2160", CYAN)],
            [("  ✓ ", GREEN), ("Windows: ", FG), ("22 visible", CYAN)],
            [("  ✓ ", GREEN), ("Safe mode: ", FG), ("ON", GREEN)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.screenshot()", PURPLE)],
        ],
        # Scene 5: screenshot result
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.status()", PURPLE)],
            [("  ✓ ", GREEN), ("Ollama: ", FG), ("connected", GREEN), ("  (mistral-small3.2)", GRAY)],
            [("  ✓ ", GREEN), ("Screen: ", FG), ("3840×2160", CYAN)],
            [("  ✓ ", GREEN), ("Windows: ", FG), ("22 visible", CYAN)],
            [("  ✓ ", GREEN), ("Safe mode: ", FG), ("ON", GREEN)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.screenshot()", PURPLE)],
            [("  ✓ ", GREEN), ("Saved: ", FG), ("demo_full.png", CYAN), (" (1920×1080)", GRAY)],
        ],
        # Scene 6: describe call
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.status()", PURPLE)],
            [("  ✓ ", GREEN), ("Ollama: ", FG), ("connected", GREEN), ("  (mistral-small3.2)", GRAY)],
            [("  ✓ ", GREEN), ("Screen: ", FG), ("3840×2160", CYAN)],
            [("  ✓ ", GREEN), ("Windows: ", FG), ("22 visible", CYAN)],
            [("  ✓ ", GREEN), ("Safe mode: ", FG), ("ON", GREEN)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.screenshot()", PURPLE)],
            [("  ✓ ", GREEN), ("Saved: ", FG), ("demo_full.png", CYAN), (" (1920×1080)", GRAY)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.describe()", PURPLE)],
            [("  ⏳ ", YELLOW), ("Analyzing with Vision LLM...", GRAY)],
        ],
        # Scene 7: describe result
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Check system status"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.status()", PURPLE)],
            [("  ✓ ", GREEN), ("Ollama: ", FG), ("connected", GREEN), ("  (mistral-small3.2)", GRAY)],
            [("  ✓ ", GREEN), ("Screen: ", FG), ("3840×2160", CYAN)],
            [("  ✓ ", GREEN), ("Windows: ", FG), ("22 visible", CYAN)],
            [("  ✓ ", GREEN), ("Safe mode: ", FG), ("ON", GREEN)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.screenshot()", PURPLE)],
            [("  ✓ ", GREEN), ("Saved: ", FG), ("demo_full.png", CYAN), (" (1920×1080)", GRAY)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.describe()", PURPLE)],
            [("  ✓ ", GREEN), ("Vision LLM analysis complete", GREEN)],
            [("", FG)],
            [("  ", FG), ('"The screen shows a terminal window with', FG)],
            [("   ", FG), ("Claude Code running, alongside a Chrome", FG)],
            [("   ", FG), ("browser with LinkedIn and a puzzle game.", FG)],
            [("   ", FG), ("Multiple sticky notes and Explorer windows", FG)],
            [("   ", FG), ('are visible on the taskbar."', FG)],
        ],
        # Scene 8: auto command
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Open Notepad and type hello"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.auto(", PURPLE)],
            [("  ", FG), ('  instruction=', GRAY), ('"Open Notepad and type hello"', YELLOW)],
            [("  ", FG), (")", PURPLE)],
        ],
        # Scene 9: auto steps
        [
            [("$ ", GREEN), ("claude", BLUE), (" -p ", FG), ('"Open Notepad and type hello"', YELLOW)],
            [("", FG)],
            [("⚡ ", CYAN), ("Calling tool: ", GRAY), ("helix-pilot.auto(", PURPLE)],
            [("  ", FG), ('  instruction=', GRAY), ('"Open Notepad and type hello"', YELLOW)],
            [("  ", FG), (")", PURPLE)],
            [("", FG)],
            [("  Step 1: ", BLUE), ("hotkey(", PURPLE), ("keys=", GRAY), ('"win"', YELLOW), (")", PURPLE)],
            [("  Step 2: ", BLUE), ("type_text(", PURPLE), ("text=", GRAY), ('"notepad"', YELLOW), (")", PURPLE)],
            [("  Step 3: ", BLUE), ("hotkey(", PURPLE), ("keys=", GRAY), ('"enter"', YELLOW), (")", PURPLE)],
            [("  Step 4: ", BLUE), ("wait_stable(", PURPLE), ("timeout=", GRAY), ("5", CYAN), (")", PURPLE)],
            [("  Step 5: ", BLUE), ("type_text(", PURPLE), ("text=", GRAY), ('"hello"', YELLOW), (")", PURPLE)],
            [("", FG)],
            [("  ✓ ", GREEN), ("5 actions executed successfully", GREEN)],
        ],
    ]

    # Frame durations (ms) — longer pause on results
    durations = [1500, 800, 1500, 800, 1500, 800, 3000, 1000, 2500]

    frames = []
    for scene in scenes:
        frames.append(render_frame(scene, font))

    # Save as GIF
    gif_path = OUT_DIR / "mcp_demo.gif"
    frames[0].save(
        str(gif_path),
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    size_kb = gif_path.stat().st_size / 1024
    print(f"✅ {gif_path.name} ({size_kb:.0f}KB)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    create_demo_gif()
