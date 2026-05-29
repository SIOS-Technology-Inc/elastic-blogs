#!/bin/bash
# ngrok tunnel のみを起動する (long-running)
#
# 用途:
#   ngrok を 1 つのターミナルで起動しっぱなしにし、別ターミナルで MCP server を
#   再起動しても ngrok URL が変わらないようにする。
#   → Kibana 側の MCP connector 設定は一度だけで済む。
#
# 使い方:
#   bash agent/start_ngrok.sh
#       → ランダムパスワードを生成
#   NGROK_AUTH="samadmin:imagepoc2026" bash agent/start_ngrok.sh
#       → 自分で決めたパスワードを使う
#
# 停止: Ctrl+C で tunnel が閉じ、URL が失われる
#       (再起動すると free 版は新しい URL になる)

cd "$(dirname "$0")/.."

# パスワードを準備
if [ -z "$NGROK_AUTH" ]; then
    PASSWORD=$(openssl rand -hex 8)
    NGROK_AUTH="poc:$PASSWORD"
fi

echo "============================================================"
echo "  ngrok tunnel only — keep this running all session"
echo "============================================================"
echo ""
echo "🔐 Basic auth: $NGROK_AUTH"
echo "💾 /tmp/mcp_demo_auth.txt にも保存"
echo "$NGROK_AUTH" > /tmp/mcp_demo_auth.txt
chmod 600 /tmp/mcp_demo_auth.txt  # 自分以外読めないようにする (security review H2)
echo ""
echo "別ターミナルで MCP server を起動してください:"
echo "  bash agent/start_mcp.sh"
echo ""
echo "停止は Ctrl+C (URL は失われる)"
echo "============================================================"
echo ""

# Ctrl+C で停止したら認証ファイルを消す (security review H2)
cleanup() {
    rm -f /tmp/mcp_demo_auth.txt
    echo ""
    echo "🗑  /tmp/mcp_demo_auth.txt を削除しました"
    exit 0
}
trap cleanup INT TERM

ngrok http 8080 --basic-auth "$NGROK_AUTH"
