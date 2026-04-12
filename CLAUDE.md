# CLAUDE.md — helix-pilot

## プロジェクト概要

helix-pilot は、ローカル Vision LLM (Ollama) でホスト OS 上のウィンドウを直接操作する
GUI 自動操作 MCP サーバーです。GitHub 公開してスター獲得を目指します。

## 技術スタック

- Python 3.12 + uv（パッケージ管理）
- FastMCP（MCP サーバー実装）
- Ollama Vision LLM（画面解析: mistral-small3.2 等）
- PyAutoGUI / Windows SendInput（操作実行）

## 共有記憶（Mem0）

Mem0 MCP サーバーが接続されています。
Qdrant コレクション名は **`mem0_shared`** で全ツール統一（詳細は AGENTS.md 参照）。

- 過去の決定や方針を確認したい時は `search_memory` で検索すること
- ユーザーが「覚えておいて」と言ったら `add_memory` で保存すること

## 開発ルール

- 日本語で応答すること
- コード・コミットメッセージ・README は英語
- UTF-8 エンコーディング必須
- テストは pytest で作成
- `uv run pytest` でテスト実行
- `uv run python -m py_compile <file>` で構文チェック

## 競合情報

- UI-TARS Desktop (ByteDance): GUI アプリ。MCP 対応済み。ただし CLI ではない
- Peekaboo: CLI + MCP + Ollama だが macOS 専用
- Cua: VM 内操作。ホスト OS 直接操作ではない
→ Windows + CLI + MCP + Ollama Vision の組み合わせは helix-pilot のみ

## ゴール

1. FastMCP でMCPサーバーとして実装
2. GitHub に公開（英語 README）
3. Stars 獲得 → 転職活動に活用
