---
title: "【ハンズオン】ローカルOllama Vision LLMでWindows GUIを自動操作するMCPサーバーを動かす"
tags: ["MCP", "Ollama", "Python", "Windows", "自動化"]
---

Claude Code や Cursor で**ブラウザ操作**はできるようになった。
でも **Premiere Pro** や **Excel** はどうする？

この記事では、ローカル Vision LLM（Ollama）を使って Windows デスクトップアプリを AI エージェントに操作させる MCP サーバー「**helix-pilot**」を、手元で動かすまでの手順を解説します。

**クラウド API 不要。データは一切外部に送信されません。**

## 前提環境

| 項目 | 要件 |
|------|------|
| OS | Windows 10/11 |
| Python | 3.12 以上 |
| GPU | VRAM 4GB 以上（CPU のみでも動作可） |
| Ollama | インストール済み |

## Step 1: Ollama で Vision モデルを取得

```bash
# 推奨: mistral-small3.2（7B, 高品質）
ollama pull mistral-small3.2

# 軽量: moondream（1.8B, CPU でも動く）
ollama pull moondream

# 高精度: gemma3:27b（VRAM 16GB 以上推奨）
ollama pull gemma3:27b
```

### モデル選択の目安

| モデル | VRAM | 速度 | 精度 | 推奨用途 |
|--------|------|------|------|---------|
| moondream | ~2GB | 速い | ★★ | 軽量テスト、CPU環境 |
| mistral-small3.2 | ~5GB | 中速 | ★★★★ | 日常使い、バランス型 |
| gemma3:27b | ~16GB | やや遅い | ★★★★★ | 複雑なUI操作 |

## Step 2: helix-pilot をセットアップ

```bash
git clone https://github.com/tsunamayo7/helix-pilot.git
cd helix-pilot
uv sync
```

## Step 3: Claude Code に接続

`~/.claude/settings.json` に以下を追加:

```json
{
  "mcpServers": {
    "helix-pilot": {
      "command": "uv",
      "args": ["run", "--directory", "C:/path/to/helix-pilot", "python", "server.py"]
    }
  }
}
```

Claude Code を再起動すると、20 個の MCP ツールが使えるようになります。

## Step 4: 実際に操作してみる

### 例1: メモ帳を開いてテキスト入力

Claude Code で以下のように指示するだけ:

```
メモ帳を開いて「Hello from helix-pilot!」と入力して
```

helix-pilot が内部で行うこと:

1. `screenshot()` — 画面キャプチャ
2. `describe()` — Vision LLM が画面内容を解析
3. `auto()` — 操作計画を立てて実行（クリック、テキスト入力）

### 例2: ファイルエクスプローラーでフォルダ移動

```
エクスプローラーで Documents フォルダを開いて
```

### 例3: 設定アプリの操作

```
Windows の設定を開いて、ディスプレイの解像度を確認して
```

## 提供される MCP ツール一覧

| ツール | 説明 |
|--------|------|
| `screenshot` | 画面キャプチャ（DPI 対応） |
| `click` | マウスクリック（左/右/ダブル） |
| `type_text` | テキスト入力 |
| `hotkey` | キーボードショートカット |
| `scroll` | スクロール操作 |
| `describe` | Vision LLM による画面解析 |
| `find` | 画面上の UI 要素を座標特定 |
| `verify` | 操作結果の検証 |
| `status` | システム状態確認 |
| `list_windows` | ウィンドウ一覧 |
| `wait_stable` | 画面安定待機 |
| `auto` | 自然言語指示 → 自動実行 |
| `browse` | ブラウザ特化の自動操作 |
| `click_screenshot` | クリック直後にスクリーンショット |
| `resize_image` | モデル入力サイズ向け画像リサイズ |
| `spawn_pilot_agent` | 常駐 GUI ワーカーを起動 |
| `send_pilot_agent_input` | ワーカーへ追加指示を送信 |
| `wait_pilot_agent` | ワーカーのターン完了を待機 |
| `list_pilot_agents` | 起動中のワーカー一覧 |
| `close_pilot_agent` | アイドル状態のワーカーを終了 |

## セキュリティ機能

helix-pilot は、デスクトップ操作を扱うツールとして次のような安全機能を組み込んでいます。

- **アクションポリシー**: サイトやコンテキスト単位で許可/拒否するアクション（click, type, submit, publish 等）を設定できます
- **シークレットスクラブ**: `.env` や `secrets/` 配下など、センシティブなパスの内容を型入力からブロックし、API キーらしき文字列も検出します

この 2 つは README に詳細な設定例があります。緊急停止（画面隅にマウスを移動）やユーザー操作の検知といった追加レイヤーはランタイム内の `SafetyGuard` に実装されているため、興味がある方はリポジトリ内のコードを参照してください。

## 他ツールとの比較

| 特徴 | helix-pilot | Peekaboo (macOS only) | Cua | UI-TARS Desktop |
|------|:-----------:|:--------:|:---:|:---------------:|
| Windows ホスト直接制御 | **Yes** | No | No (VM) | Yes |
| ローカル Vision LLM | **Yes** | Yes | No | No |
| MCP サーバー | **Yes** | Yes | No | Partial |
| API 費用ゼロ | **Yes** | Yes | No | No |
| 安全機能内蔵 | **Yes** | No | Partial | No |

## まとめ

helix-pilot を使えば、Claude Code や Cursor から **Windows のあらゆるデスクトップアプリ**を AI に操作させることができます。ローカル完結なので:

- API 費用がかからない
- 機密データが外部に送信されない
- ネットワーク不要で動作する

興味があれば Star をお願いします:
**https://github.com/tsunamayo7/helix-pilot**

## 参考リンク

- [MCP 公式サイト](https://modelcontextprotocol.io)
- [Ollama 公式サイト](https://ollama.com)
- [FastMCP ライブラリ](https://github.com/jlowin/fastmcp)
