"""
alias を v2 → v1 にアトミックに戻すスクリプト

理由 (経緯):
  - v2 は semantic_text フィールドを試した実験版
  - semantic_text は base64 をテキストとして埋め込んでしまい、画像検索の精度が大きく劣化
  - v1 (dense_vector + 手動 content-block _inference) は正常に動作していたため戻す
  - v2 インデックス自体は削除しない (将来の検証用に残す)

使い方:
    python setup/revert_alias_to_v1.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

ELASTIC_URL = os.environ["ELASTIC_URL"].strip()
ELASTIC_API_KEY = os.environ["ELASTIC_API_KEY"].strip()
INDEX_NAME = os.environ["INDEX_NAME"].strip()

ALIAS = INDEX_NAME
V1 = f"{INDEX_NAME}-v1"
V2 = f"{INDEX_NAME}-v2"

es = Elasticsearch(
    hosts=[ELASTIC_URL],
    api_key=ELASTIC_API_KEY,
    request_timeout=30,
)

print("============================================================")
print("  alias を v2 → v1 に戻す")
print("============================================================\n")

# 現在の alias 状態を確認
try:
    current = es.indices.get_alias(name=ALIAS)
    pointing_to = list(current.keys())
    print(f"現在 alias '{ALIAS}' が指しているインデックス: {pointing_to}")
except Exception as e:
    print(f"❌ alias '{ALIAS}' が見つかりません: {e}")
    sys.exit(1)

# v1 がまだ存在するか確認
if not es.indices.exists(index=V1):
    print(f"❌ {V1} が存在しません。alias を戻せません。")
    sys.exit(1)
print(f"✅ {V1} は存在する (戻し先 OK)\n")

# アトミックに付け替え
actions = []
for current_index in pointing_to:
    if current_index != V1:
        actions.append({"remove": {"index": current_index, "alias": ALIAS}})
if V1 not in pointing_to:
    actions.append({"add": {"index": V1, "alias": ALIAS}})

if not actions:
    print(f"✅ alias '{ALIAS}' は既に '{V1}' を指しています (何もしない)")
    sys.exit(0)

print(f"▶ アトミック付け替えを実行中...")
print(f"   アクション: {actions}")
es.indices.update_aliases(actions=actions)
print(f"✅ alias '{ALIAS}' → '{V1}' に戻しました\n")

print("🎉 完了！アプリ側のクエリは alias '" + ALIAS + "' を通して自動的に v1 を使うようになりました。")
print(f"   v2 ({V2}) は実験記録として残してあります (DELETE で削除可)。")
