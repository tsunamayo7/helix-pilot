# helix-pilot コンテンツ戦略 — 全プラットフォーム調査に基づく記事構成

> 2026-03-28 作成 — 9プラットフォーム調査結果を統合

---

## 調査で判明した核心的事実

| 発見 | データ |
|------|--------|
| Zenn MCP トピック | 2,222記事、Claude Code トピック 4,305記事 — 非常に活発 |
| バズる記事の長さ | **3,000字前後**が最もいいね率が高い（長文より短い方がバズる） |
| r/LocalLLaMA 最強訴求 | ローカル実行 + API費用ゼロ + ハードウェアスペック明記 |
| HN 成功の鍵 | Show HN + 火〜木 8-10AM PT + コメント即応答 |
| Product Hunt | デモGIF必須、60字タグライン、火〜木 00:01 PST |
| 全プラットフォーム共通 | **デモGIF/動画は必須** — 「見せる」ことが信頼性を桁違いに上げる |

---

## helix-pilot の差別化ポイント（全記事で一貫して訴求）

1. **100% ローカル** — Ollama Vision LLM、API費用ゼロ、データ外部送信なし
2. **Windows ネイティブ** — ホスト OS 直接操作（VM でもコンテナでもない）
3. **MCP ネイティブ** — Claude Code / Codex CLI / Cursor から即座に使える
4. **安全設計** — アクション制御、シークレット検出、緊急停止

---

## 記事プラン（優先順）

---

### 記事1: Zenn（最優先 — 最もバズりやすい）

**タイトル案（パターン: ストーリー型 + 具体性）**
```
ローカル Vision LLM でデスクトップを AI に操作させる MCP サーバーを作った
```

**サブタイトル**
```
Ollama + FastMCP で Windows GUI 自動化 — API 費用ゼロで Claude Code から操作
```

**構成（目標: 3,000〜3,500字）**

```
## はじめに（フック — 問題提示型）
「Claude Code でブラウザ操作はできる。でも Premiere Pro や Excel は？」
→ 既存ツールの限界を提示（macOS専用、VM内、クラウドAPI必須）
→ 「全部ローカルで解決する MCP サーバーを作った」

## helix-pilot とは
- 1行説明 + アーキテクチャ図
- 15個のMCPツール一覧（表形式）
- デモGIF（status → screenshot → describe → auto の流れ）

## なぜローカル Vision LLM なのか
- クラウド API のコスト問題（GPT-4V: $0.01/image → 1日100回で月$30）
- プライバシー（画面キャプチャをクラウドに送る怖さ）
- レイテンシ（ローカルなら 1-3秒、クラウドなら 5-10秒）
- Ollama の Vision モデル比較表（gemma3:27b, mistral-small3.2, llava）

## 動かしてみる（クイックスタート）
- 3ステップ: ollama pull → git clone → uv sync
- Claude Code の設定 JSON（コピペ可能）
- 実行例: 「メモ帳を開いて Hello World と入力」

## 安全設計
- なぜ GUI 自動化に安全機構が必要か
- 緊急停止（マウスを画面隅に移動）
- シークレット検出（API キーの入力をブロック）
- ウィンドウ拒否リスト（Task Manager 等を保護）

## 競合との比較（表形式）
- helix-pilot vs terminator vs UI-TARS Desktop vs Peekaboo vs Cua
- （README の表をそのまま活用）

## まとめ
- GitHub リンク + Star お願い
- 「試してフィードバックください」で行動喚起
```

**投稿時の設定**
- トピック: `mcp`, `claudecode`, `ollama`, `python`, `windows`
- 公開タイミング: 平日朝 8-10時

---

### 記事2: r/LocalLLaMA（英語圏で最もリーチが大きい）

**タイトル**
```
I built an MCP server that automates any Windows desktop app using local Ollama Vision models — zero cloud API cost
```

**本文構成（Reddit投稿スタイル）**
```
## What it does
1行: helix-pilot lets AI agents see and control your Windows desktop
through MCP, using only local Ollama vision models.

## Demo
[GIF: Notepad自動操作 or Excel操作]

## Hardware
- Tested on: RTX 5070 Ti (16GB), RTX PRO 6000 (96GB)
- Minimum: Any GPU that can run llava or moondream (4GB VRAM)
- inference speed: ~2-4 sec/screenshot on mistral-small3.2

## How it works
- FastMCP server → 15 tools (screenshot, click, type, find, auto...)
- Ollama Vision LLM analyzes screenshots locally
- Win32 API + PyAutoGUI for mouse/keyboard control
- Safety: action policies, secret detection, emergency stop

## vs Alternatives
| Feature | helix-pilot | terminator | Peekaboo | Cua |
|---------|:-----------:|:----------:|:--------:|:---:|
| Local Vision LLM | Yes | No | Yes | No |
| Windows native | Yes | Yes | No (macOS) | No (VM) |
| MCP server | Yes | No | Yes | No |
| Zero API cost | Yes | No | Yes | No |

## Try it
GitHub: [link]
3 commands: ollama pull → git clone → uv sync

Feedback welcome — especially on vision model accuracy
and what desktop apps you'd want to automate.
```

**投稿タイミング**: 火〜木、8-10AM PT
**コメント戦略**: 投稿後30分以内に全コメントに返信

---

### 記事3: X (Twitter) スレッド

**フック（1ツイート目）**
```
I built an MCP server that lets Claude Code
see and control my Windows desktop.

No cloud APIs. No VM. Just local Ollama.

Here's how it works (and you can try it now): 🧵
```

**スレッド構成（7ツイート）**
```
1/ [フック — 上記]

2/ The problem:
   - Browser automation? Solved (Playwright, etc.)
   - But what about Premiere Pro? Excel? Any native app?
   - Existing tools: macOS only, VM-based, or need cloud APIs
   [画像: 比較表]

3/ helix-pilot = MCP server + local Vision LLM
   - Captures screenshots
   - Ollama analyzes what's on screen
   - Executes mouse/keyboard actions
   - All on YOUR machine
   [GIF: auto() でメモ帳操作]

4/ 15 tools available via MCP:
   screenshot, click, type, hotkey, scroll,
   describe, find, verify, auto, browse...

   Works with Claude Code, Codex CLI, Cursor, Open WebUI
   [画像: ツール一覧]

5/ Safety-first design:
   - Emergency stop (mouse to corner)
   - Secret detection (blocks API keys from being typed)
   - Window deny list (protects Task Manager, etc.)
   - Execution modes: observe_only → draft_only → apply_with_approval

6/ Zero cost to run:
   - Ollama: free
   - Vision models: gemma3:27b, mistral-small3.2, llava
   - No API keys needed
   - No data leaves your PC

7/ Try it now:
   ollama pull mistral-small3.2
   git clone [repo]
   cd helix-pilot && uv sync

   GitHub: [link]
   MIT licensed.

   Star if you find it useful.
```

---

### 記事4: Hacker News（Show HN）

**タイトル**
```
Show HN: Helix-Pilot – MCP server for Windows GUI automation with local Vision LLMs
```

**本文（簡潔 — HN は短い方が良い）**
```
I built an MCP server that lets AI agents (Claude Code, Codex CLI, etc.)
see and control Windows desktop applications using local Ollama vision models.

Key differentiators:
- 100% local: Ollama Vision LLM, no cloud API calls
- Windows-native: direct host OS control via Win32 API (not VM)
- MCP-native: works with any MCP client
- 15 tools: screenshot, click, type, find, auto, browse, etc.
- Safety: action policies, secret detection, emergency stop

Tested with gemma3:27b, mistral-small3.2, and llava on RTX 5070 Ti.

GitHub: [link]

Happy to answer questions about the Vision LLM integration
and safety architecture.
```

**投稿タイミング**: 火〜木、8-10AM PT
**コメント戦略**: 技術的な質問に詳細に回答。なぜこのアーキテクチャを選んだか、VLMの精度課題など。

---

### 記事5: Dev.to（SEO + 長期トラフィック）

**タイトル**
```
How I Built an MCP Server That Automates Any Desktop App Using Local Vision LLMs
```

**構成（体験記 + チュートリアル）**
```
## The Problem
- AI coding tools can't touch native desktop apps
- Existing solutions: cloud-dependent or OS-locked

## What I Built
- helix-pilot: MCP server + Ollama Vision LLM
- Architecture diagram
- Demo GIF

## Technical Deep Dive
- FastMCP for MCP protocol
- Ollama Vision API integration
- Win32 API for GUI control
- Safety system design

## Try It Yourself
- Prerequisites
- Installation (3 commands)
- MCP client configuration
- First automation example

## Lessons Learned
- Vision LLM accuracy challenges
- Coordinate precision on 4K displays
- Why safety-first design matters

## What's Next
- GitHub link + contribution guide
```

---

### 記事6: Product Hunt ローンチ

**タグライン（60字以内）**
```
Automate any Windows app with local AI vision — zero API cost
```

**説明**
```
helix-pilot is an MCP server that lets AI agents see and control
your Windows desktop using local Ollama Vision models.
No cloud APIs, no VM — just your machine.
```

**デモ資産**
- サムネイル: 1280x720、helix-pilotロゴ + デスクトップ操作のスクリーンショット
- GIF: 30秒、status → screenshot → describe → auto の流れ
- ギャラリー: 5枚（アーキテクチャ、比較表、安全機能、MCP設定、デスクトップキャプチャ）

**Maker Comment**
```
Hi, I'm tsunamayo7. I built helix-pilot because I wanted Claude Code
to control not just my browser, but any desktop application.

Existing tools were either macOS-only, VM-based, or required
expensive cloud APIs. I wanted something that:
- Runs entirely on my machine (privacy + no API cost)
- Works with any MCP client (Claude Code, Codex CLI, Cursor)
- Is safe by design (emergency stop, secret detection)

helix-pilot uses local Ollama vision models to understand
what's on screen and execute GUI actions. It's MIT licensed
and I'd love your feedback.
```

---

### 記事7: note.com（日本語 SEO + 長期トラフィック）

**タイトル**
```
【2026年】ローカルAIでデスクトップ操作を完全自動化するMCPサーバーを作った話
```

**構成（体験記型 — note.com で最も支持される形式）**
```
## なぜ作ったのか
- AIエンジニア転職活動中 → ポートフォリオとして
- 競合分析: Peekaboo（macOS専用）、Cua（VM）、UI-TARS（CLI非対応）
- 「Windows + ローカル + MCP」の空白地帯を発見

## helix-pilot の紹介
- デモGIF
- 何ができるか（15ツール）
- アーキテクチャ

## 技術選定の理由
- なぜ FastMCP か（MCP SDK の種類と比較）
- なぜ Ollama か（クラウドAPI vs ローカルのコスト比較）
- なぜ PyAutoGUI + Win32 API か

## 開発過程で学んだこと
- Vision LLM の座標推定精度の課題と対策
- 4K ディスプレイでの DPI Awareness 問題
- 安全設計の重要性（シークレット漏洩防止）

## まとめ
- GitHub リンク
- 転職活動でどう活用するか
```

---

### 記事8: Hashnode（英語 SEO 特化）

**タイトル**
```
The Playwright for Desktop Apps: Building an MCP Server with Local Vision LLMs
```

**構成（アナロジー駆動 + SEO最適化）**
```
- Playwright automates browsers. helix-pilot automates everything else.
- チュートリアル形式
- コード例とGIFデモを交互に配置
- SEOタグ: mcp, ollama, gui-automation, windows, claude-code
```

---

## 投稿スケジュール（推奨順序）

| 週 | プラットフォーム | 記事 | 理由 |
|----|-----------------|------|------|
| Week 1 | **Zenn** | ローカル Vision LLM で...作った | 日本語コミュニティで最初の反応を得る |
| Week 1 | **X スレッド** | I built an MCP server... | Zenn記事への流入を作る |
| Week 2 | **r/LocalLLaMA** | I built an MCP server... | 英語圏のローカルLLMコミュニティ |
| Week 2 | **Dev.to** | How I Built... | SEO用の長期トラフィック記事 |
| Week 3 | **Hacker News** | Show HN: Helix-Pilot | Reddit/Dev.toでの反応を見てから |
| Week 3 | **Hashnode** | The Playwright for Desktop Apps | SEO補完 |
| Week 4 | **Product Hunt** | ローンチ | 十分なフィードバックを反映してから |
| Week 4 | **note.com** | 作った話 | 日本語SEO長期トラフィック |

---

## デモ資産の準備（全記事共通で必要）

| 資産 | 仕様 | 用途 |
|------|------|------|
| **操作デモ GIF** | 30秒、メモ帳 or Excel 自動操作 | 全プラットフォーム |
| **MCP ツール呼び出し GIF** | 20秒、status→screenshot→describe | Zenn, Dev.to, Hashnode |
| **比較表画像** | 1200x600、helix-pilot vs 競合 | X スレッド, Reddit |
| **アーキテクチャ図** | Mermaid or SVG | Zenn, Dev.to, Hashnode |
| **30秒デモ動画** | MP4、縦横両方 | Product Hunt, X |

---

## KPI目標

| プラットフォーム | 目標 |
|-----------------|------|
| Zenn | 100+ いいね |
| r/LocalLLaMA | 50+ upvotes |
| X スレッド | 100+ RT |
| Hacker News | Front page（30+ points） |
| Product Hunt | 100+ upvotes |
| GitHub Stars | 50+ （全投稿合計） |
