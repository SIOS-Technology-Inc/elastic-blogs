"""
semantic_text フィールド × 画像 base64 が動くかの先行テスト

やること:
  1. 一時テスト index 'test-semantic-image' を作る (image_content: semantic_text)
  2. 2 枚の画像を base64 化して、3 つのフォーマットを試してインデックス
  3. semantic search で検索が当たるか確認 → 動くフォーマットを特定
  4. テスト index を消す (クリーンアップ)

使い方:
    python tools/test_semantic_text_image.py <画像1> <画像2>
"""

import base64
import math
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

es = Elasticsearch(
    hosts=[os.environ["ELASTIC_URL"].strip()],
    api_key=os.environ["ELASTIC_API_KEY"].strip(),
    request_timeout=120,
)

TEST_INDEX = "test-semantic-image"
INFERENCE_ID = ".jina-embeddings-v5-omni-small"


if len(sys.argv) < 3:
    print("使い方: python tools/test_semantic_text_image.py <画像1> <画像2>")
    sys.exit(1)

p1, p2 = Path(sys.argv[1]), Path(sys.argv[2])
b64_1 = base64.b64encode(p1.read_bytes()).decode("ascii")
b64_2 = base64.b64encode(p2.read_bytes()).decode("ascii")
data_uri_1 = f"data:image/jpeg;base64,{b64_1}"
data_uri_2 = f"data:image/jpeg;base64,{b64_2}"


# ============================================================
# 後始末: 既存のテスト index を消す
# ============================================================
if es.indices.exists(index=TEST_INDEX):
    es.indices.delete(index=TEST_INDEX)
    print(f"🗑  既存の {TEST_INDEX} を削除しました")


# ============================================================
# テスト index を作成 (semantic_text フィールド)
# ============================================================
print(f"▶ テスト index {TEST_INDEX} を作成中...")
es.indices.create(
    index=TEST_INDEX,
    mappings={
        "properties": {
            "name": {"type": "keyword"},
            "image_content": {
                "type": "semantic_text",
                "inference_id": INFERENCE_ID,
            },
        }
    },
)
print(f"✅ {TEST_INDEX} 作成完了\n")


# ============================================================
# 3 種類の入力フォーマットを試して、どれが動くか確認
# ============================================================
formats = [
    ("A: 単純 base64 文字列",       b64_1,      b64_2),
    ("B: data URI 文字列",          data_uri_1, data_uri_2),
    ("C: content block オブジェクト",
        {"content": {"type": "image", "format": "base64", "value": data_uri_1}},
        {"content": {"type": "image", "format": "base64", "value": data_uri_2}}),
]

for label, val1, val2 in formats:
    print(f"━━━ {label} ━━━")
    try:
        es.index(
            index=TEST_INDEX,
            id=f"img1_{label[0]}",
            document={"name": p1.stem, "image_content": val1},
            refresh="wait_for",
        )
        es.index(
            index=TEST_INDEX,
            id=f"img2_{label[0]}",
            document={"name": p2.stem, "image_content": val2},
            refresh="wait_for",
        )
        print("   ✅ インデックス成功")
    except Exception as e:
        print(f"   ❌ インデックス失敗: {str(e)[:200]}\n")
        continue

    # semantic search で動作確認 (テキストクエリで画像が見つかるか)
    try:
        result = es.search(
            index=TEST_INDEX,
            query={
                "semantic": {
                    "field": "image_content",
                    "query": "a photo of an object",
                }
            },
            size=5,
            source=["name"],
        )
        hits = result["hits"]["hits"]
        print(f"   ✅ semantic 検索成功 → {len(hits)} 件ヒット")
        for h in hits:
            print(f"      _id={h['_id']:15s}  name={h['_source']['name']}  _score={h['_score']:.4f}")
        print()
    except Exception as e:
        print(f"   ❌ semantic 検索失敗: {str(e)[:200]}\n")


# ============================================================
# 後始末
# ============================================================
es.indices.delete(index=TEST_INDEX)
print(f"🗑  テスト index {TEST_INDEX} を削除しました")
print("\n→ 上のうち「✅ インデックス成功 + 検索結果がスコア差を持って返る」フォーマットを Phase 3 で使います。")
