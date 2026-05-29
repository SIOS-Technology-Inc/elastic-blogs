#!/bin/bash
# Demo セッション用: MCP server と ngrok を一度に起動し、Ctrl+C で両方止める
#
# ⚠️ ファイルを編集しながら開発するときは、こちらの「一体型」より
#    start_ngrok.sh + start_mcp.sh の 2 ターミナル運用を推奨。
#    そうすれば MCP server を再起動しても ngrok URL は変わらず、
#    Kibana 側の MCP connector 設定を毎回直す必要がない。
#
# 使い方:
#     bash agent/start_demo.sh
#
# 何が起こるか:
#   1. MCP server をバックグラウンドで :8080 に起動
#   2. ngrok を basic-auth 付きで起動 (毎回ランダムなパスワード)
#   3. tunnel URL と認証情報を表示
#   4. Ctrl+C で両方ともクリーンに停止
#
# 事前準備:
#   - brew install ngrok
#   - ngrok config add-authtoken <YOUR_TOKEN>  (https://dashboard.ngrok.com で取得)

cd "$(dirname "$0")/.."

# ============================================================
# basic auth の認証情報を毎回ランダム生成 (=漏れても被害最小)
# 環境変数 NGROK_AUTH があればそれを使う
# ============================================================
if [ -z "$NGROK_AUTH" ]; then
    PASSWORD=$(openssl rand -hex 8)
    NGROK_AUTH="poc:$PASSWORD"
fi

echo "============================================================"
echo "  Image Search PoC — Demo セッション開始"
echo "============================================================"
echo ""
echo "🔐 Basic auth: $NGROK_AUTH"
echo "   ↑ これを Agent Builder の Manage MCP に入れます"
echo ""

# 認証情報を一時ファイルに保存 (ngrok が画面を占有しても後から確認できる)
echo "$NGROK_AUTH" > /tmp/mcp_demo_auth.txt
chmod 600 /tmp/mcp_demo_auth.txt  # security review H2: 自分以外読めないように
echo "💾 認証情報は /tmp/mcp_demo_auth.txt にも保存されています (chmod 600)"
echo "   別ターミナルで 'cat /tmp/mcp_demo_auth.txt' で確認可能"
echo ""

# ============================================================
# MCP server をバックグラウンドで起動
# ============================================================
echo "▶ MCP server を起動中..."
touch /tmp/mcp_server.log
chmod 600 /tmp/mcp_server.log  # security review L4: ログを他ユーザーから守る
./venv/bin/python agent/mcp_server.py > /tmp/mcp_server.log 2>&1 &
MCP_PID=$!
sleep 2

# サーバーが起動したか確認
if ! kill -0 $MCP_PID 2>/dev/null; then
    echo "❌ MCP server の起動に失敗しました。/tmp/mcp_server.log を確認してください。"
    cat /tmp/mcp_server.log
    exit 1
fi
echo "✅ MCP server: http://localhost:8080/mcp  (PID $MCP_PID)"
echo ""

# ============================================================
# Ctrl+C で両方とも止めるトラップ
# ============================================================
cleanup() {
    echo ""
    echo "🛑 停止しています..."
    kill $MCP_PID 2>/dev/null
    wait $MCP_PID 2>/dev/null
    echo "✅ MCP server 停止"
    echo "✅ ngrok tunnel 停止"
    # security review H2: 認証情報の残骸を消す
    rm -f /tmp/mcp_demo_auth.txt /tmp/mcp_server.log
    echo "🗑  /tmp の認証情報・ログを削除しました"
    echo ""
    echo "ご利用ありがとうございました。"
    exit 0
}
trap cleanup INT TERM

# ============================================================
# ngrok を foreground で起動 (basic-auth 付き)
# ============================================================
echo "▶ ngrok tunnel を起動します..."
echo "   表示される 'Forwarding https://...ngrok-free.app' を控えてください"
echo "   この URL + 上の認証情報を Manage MCP に登録する"
echo ""
echo "   止めるときは Ctrl+C → MCP server も一緒に止まります"
echo "============================================================"
echo ""

ngrok http 8080 --basic-auth "$NGROK_AUTH"

# ngrok が抜けたらクリーンアップ
cleanup
