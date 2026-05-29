"""
Phase 2: dense_vector を使ったインデックスを作るスクリプト

このスクリプトが何をするか:
  1. .env から接続情報を読み込む
  2. 実体インデックス <INDEX_NAME>-v1 を作る
     - image_embedding は dense_vector(1024) / cosine / int8_hnsw
  3. alias <INDEX_NAME> を v1 に紐づける

設計メモ (semantic_text を試した経緯あり):
  Phase 5 の途中で semantic_text を試したが、画像 base64 を「テキスト」として扱われ、
  検索精度が大きく劣化した (詳細は WALKTHROUGH.md)。dense_vector + content-block 形式の
  _inference を Python から呼ぶアプローチが正しい。

使い方:
    source venv/bin/activate
    python setup/create_elastic_index.py

このスクリプトは何度実行しても安全 (idempotent)。
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


# ============================================================
# ステップ 1: .env を読み込む
# ============================================================
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

ELASTIC_URL = os.environ.get("ELASTIC_URL", "").strip()
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY", "").strip()
INDEX_NAME = os.environ.get("INDEX_NAME", "").strip()

if not ELASTIC_URL or not ELASTIC_API_KEY or not INDEX_NAME:
    print("❌ .env の ELASTIC_URL / ELASTIC_API_KEY / INDEX_NAME のどれかが未設定です。")
    sys.exit(1)

ALIAS_NAME = INDEX_NAME
REAL_INDEX = f"{INDEX_NAME}-v1"

print("============================================================")
print("  Phase 2: Elastic にインデックスを作る")
print("============================================================\n")
print(f"📚 実体インデックス: {REAL_INDEX}")
print(f"🔖 alias 名:         {ALIAS_NAME}\n")


# ============================================================
# ステップ 2: Elasticsearch に接続
# ============================================================
es = Elasticsearch(
    hosts=[ELASTIC_URL],
    api_key=ELASTIC_API_KEY,
    request_timeout=30,
)

print("▶ 接続を確認中...")
try:
    info = es.info()
    print(f"✅ 接続成功 (バージョン: {info['version']['number']})\n")
except Exception as e:
    print(f"❌ 接続に失敗しました: {e}")
    sys.exit(1)


# ============================================================
# ステップ 3: 実体インデックスを作成
# ============================================================
mapping = {
    "properties": {
        "image_key":   {"type": "keyword"},
        "name":        {"type": "text"},
        "description": {"type": "text"},
        "image_embedding": {
            "type": "dense_vector",
            "dims": 1024,             # Jina v5 omni small の出力次元
            "index": True,
            "similarity": "cosine",   # Jina 推奨
            "index_options": {"type": "int8_hnsw"},  # メモリ約 1/4
        },
    }
}

if es.indices.exists(index=REAL_INDEX):
    print(f"✅ 実体インデックス '{REAL_INDEX}' は既にあります (作成スキップ)\n")
else:
    print(f"▶ 実体インデックス '{REAL_INDEX}' を作成中...")
    es.indices.create(index=REAL_INDEX, mappings=mapping)
    print(f"✅ '{REAL_INDEX}' を作成しました")
    print("   (image_embedding: dense_vector / 1024dims / cosine / int8_hnsw)\n")


# ============================================================
# ステップ 4: alias を紐づける
# ============================================================
# 注意: alias と同じ名前の実体インデックスがあるとぶつかる
if es.indices.exists(index=ALIAS_NAME) and not es.indices.exists_alias(name=ALIAS_NAME):
    print(f"❌ '{ALIAS_NAME}' という実体インデックスが既に存在します。")
    print("   alias を作るには、その実体を削除するか別の名前を選んでください。")
    sys.exit(1)

print(f"▶ alias '{ALIAS_NAME}' を '{REAL_INDEX}' に紐づけています...")
es.indices.put_alias(index=REAL_INDEX, name=ALIAS_NAME)
print(f"✅ alias '{ALIAS_NAME}' → '{REAL_INDEX}'\n")


# ============================================================
# ステップ 5: 最終確認
# ============================================================
print("▶ 最終確認:")
mapping_result = es.indices.get_mapping(index=REAL_INDEX)
props = mapping_result[REAL_INDEX]["mappings"]["properties"]
emb = props["image_embedding"]
print(f"  ✅ {REAL_INDEX} のフィールド:")
print(f"     - image_key:       keyword")
print(f"     - name:            text")
print(f"     - description:     text")
print(
    f"     - image_embedding: dense_vector / "
    f"{emb['dims']}dim / {emb['similarity']} / {emb['index_options']['type']}"
)

aliases = es.indices.get_alias(name=ALIAS_NAME)
for idx in aliases:
    print(f"  ✅ alias '{ALIAS_NAME}' → '{idx}'")

print("\n🎉 Phase 2 完了！次は Phase 3 (画像 ingest) に進めます。")
