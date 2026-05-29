"""
2つの inference エンドポイント × 3種類の入力で挙動を比較する

確認したいこと:
  - .jina-embeddings-v5-omni-small か .jina-clip-v2 のどちらが URL を画像として処理するか?
  - public な Unsplash URL なら処理されるのか? (S3 の pre-signed URL の問題切り分け)

判定方法 (各エンドポイントごと):
  - 「猫の Unsplash URL」と「犬の Unsplash URL」の embedding を比べる
  - 違う画像なら cosine < 0.85 になるはず (これが GOOD)
  - 一緒だと cosine ≈ 1 (どちらも URL テキストとして埋め込まれている = BAD)
  - テキスト "cat" との類似度も見て、ちゃんと意味と合っているか確認

使い方:
    python tools/test_endpoint_options.py
"""

import math
import os
from pathlib import Path

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


# ============================================================
# 共通設定
# ============================================================
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

es = Elasticsearch(
    hosts=[os.environ["ELASTIC_URL"].strip()],
    api_key=os.environ["ELASTIC_API_KEY"].strip(),
    request_timeout=60,
)


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def embed(inference_id, value):
    """指定したエンドポイントで埋め込みを取得する"""
    resp = es.inference.inference(inference_id=inference_id, input=[value])
    for key in ("embeddings", "text_embedding", "embedding"):
        if key in resp and len(resp[key]) > 0:
            first = resp[key][0]
            return first["embedding"] if isinstance(first, dict) else first
    raise ValueError(f"embedding なし。キー: {list(resp.keys())}")


# ============================================================
# テスト用の入力
# ============================================================
# Unsplash の公開画像 URL (誰でもアクセス可能・auth 不要)
CAT_URL = "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400"
DOG_URL = "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=400"
CAT_TEXT = "a photo of a cat"

ENDPOINTS = [
    ".jina-embeddings-v5-omni-small",
    ".jina-clip-v2",
]


# ============================================================
# 各エンドポイントを試す
# ============================================================
print("============================================================")
print("  エンドポイント × 入力フォーマット 比較")
print("============================================================\n")

for endpoint in ENDPOINTS:
    print(f"▶ エンドポイント: {endpoint}")
    try:
        cat_emb = embed(endpoint, CAT_URL)
        dog_emb = embed(endpoint, DOG_URL)
        cat_text_emb = embed(endpoint, CAT_TEXT)

        sim_cat_dog = cosine(cat_emb, dog_emb)
        sim_cattext_cat = cosine(cat_text_emb, cat_emb)
        sim_cattext_dog = cosine(cat_text_emb, dog_emb)

        print(f"   cosine(猫URL, 犬URL)            = {sim_cat_dog:.4f}")
        print(f"   cosine('a photo of a cat', 猫URL) = {sim_cattext_cat:.4f}")
        print(f"   cosine('a photo of a cat', 犬URL) = {sim_cattext_dog:.4f}")

        # 評価
        urls_distinct = sim_cat_dog < 0.85
        text_picks_cat = sim_cattext_cat > sim_cattext_dog + 0.05

        if urls_distinct and text_picks_cat:
            print("   ✅ このエンドポイントは URL を画像として正しく処理している!\n")
        elif urls_distinct:
            print("   ⚠️  URL は区別されているが、テキストと意味的に一致していない\n")
        else:
            print("   ❌ URL を画像として処理していない (テキスト扱い)\n")

    except Exception as e:
        print(f"   ❌ エラー: {str(e)[:200]}\n")
