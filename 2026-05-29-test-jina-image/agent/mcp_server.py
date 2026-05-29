"""
MCP サーバー: tools/search_tools.py の 3 つの検索関数を MCP ツールとして公開する

なぜ MCP か:
  Elastic Agent Builder の Tool タイプは ES|QL / Index search / Workflow / MCP の 4 つ。
  前者 3 つは「テキスト → ベクトル → kNN」という 1ステップ操作ができない
  (ES|QL は query_vector_builder を持たない、Index search は LLM が ES|QL を生成するだけ)。
  MCP は Agent Builder 公式サポートのカスタムツール接続なので、Python wrapper を載せても
  Elastic-native な統合になる。

起動方法:
  HTTP モード (Agent Builder からアクセスする用):
    ./venv/bin/python agent/mcp_server.py
    → 0.0.0.0:8080 で待ち受け

  stdio モード (Claude Desktop など、ローカルで試したいとき):
    ./venv/bin/python agent/mcp_server.py --stdio

Agent Builder からアクセスするには、外部からこのサーバーに HTTPS で到達できる必要がある。
ローカルで試すなら ngrok を使う:
    brew install ngrok
    ngrok http 8080
  → ngrok が https://<random>.ngrok.app の URL を返す。これを Agent Builder の
     "Manage MCP" に登録する。
"""

import sys
from pathlib import Path

# project root を import path に追加 (tools/ を import するため)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

from tools.search_tools import (
    search_by_text,
    search_by_filename,
    search_by_text_in_image,
)


# ============================================================
# MCP サーバーを定義
# ============================================================
mcp = FastMCP("image-search-poc")


# ============================================================
# ツール 1: 自然言語で画像を検索
# ============================================================
@mcp.tool()
def search_images_by_text(query: str) -> list:
    """
    自然言語のクエリで画像を意味検索する。日本語・英語どちらでも可。

    Args:
        query: 探したい画像の説明。例: "赤い椅子", "taxi at night", "グループディスカッション"

    Returns:
        最大 3 件の {name, score, image_url} 形式の結果リスト。
        image_url は 1 時間有効の pre-signed S3 URL なので、そのまま markdown 画像として
        表示できる。
    """
    return search_by_text(query)


# ============================================================
# ツール 2: 既存ファイル名から類似画像を検索
# ============================================================
@mcp.tool()
def search_images_by_filename(filename: str) -> list:
    """
    既にインデックスされている画像のファイル名を基に、視覚的に似た画像を検索する。
    自分自身は結果から除外される。

    Args:
        filename: 既存画像のファイル名 (例: "IMG_8133.jpeg")

    Returns:
        最大 3 件の {name, score, image_url} 形式の結果リスト。
    """
    return search_by_filename(filename)


# ============================================================
# ツール 3: 画像内に書かれている文字で検索
# ============================================================
@mcp.tool()
def search_images_by_visible_text(visible_text: str) -> list:
    """
    画像の中に写っている文字 (看板・表記など) を含む画像を検索する。

    Args:
        visible_text: 画像内に見えるはずの文字列。例: "SOLD", "営業中"

    Returns:
        最大 3 件の {name, score, image_url} 形式の結果リスト。
    """
    return search_by_text_in_image(visible_text)


# ============================================================
# サーバー起動
# ============================================================
if __name__ == "__main__":
    use_stdio = "--stdio" in sys.argv

    if use_stdio:
        # ローカルクライアント (Claude Desktop など) から呼ぶ用
        print("📡 MCP server on stdio (for local clients)", file=sys.stderr)
        mcp.run()
    else:
        # Agent Builder は Streamable HTTP transport を使う (POST + JSON-RPC)
        # ngrok inspector で確認済み: POST /sse に initialize JSON-RPC が来る
        # → エンドポイントは /mcp で受ければよい
        # host="127.0.0.1": ローカルループバックのみで listen する。
        # ngrok はローカルへ転送するので問題なし。同じ Wi-Fi 上の他デバイスから直接
        # ポート 8080 を叩いて ngrok の認証をバイパスされるリスクを防ぐ。
        print("📡 MCP server starting on http://127.0.0.1:8080/mcp", file=sys.stderr)
        print("   → Streamable HTTP transport (POST /mcp で JSON-RPC を受ける)", file=sys.stderr)
        print("   → 外部からは ngrok URL + /mcp 経由でのみ到達可", file=sys.stderr)
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8080)
