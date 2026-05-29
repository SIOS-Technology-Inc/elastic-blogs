#!/bin/bash
# MCP server のみを起動する (再起動が高頻度)
#
# 用途:
#   ngrok は別ターミナルで動いている前提。コードを変更したら このスクリプトを
#   Ctrl+C → 再実行するだけで済む。ngrok URL は変わらないので Kibana 側の
#   MCP connector 設定はそのまま使える。
#
# 使い方:
#   bash agent/start_mcp.sh
#
# 停止: Ctrl+C

cd "$(dirname "$0")/.."

echo "============================================================"
echo "  MCP server only — restart freely without affecting ngrok"
echo "============================================================"
echo ""
echo "▶ 接続先 (内部): http://localhost:8080/mcp"
echo "▶ ngrok 経由 (外部): /tmp/mcp_demo_auth.txt + ngrok のターミナルを確認"
echo ""
echo "停止は Ctrl+C"
echo "============================================================"
echo ""

./venv/bin/python agent/mcp_server.py
