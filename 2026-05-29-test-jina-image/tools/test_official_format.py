"""
Elastic 公式ドキュメントで確認した multimodal content block 形式をテストする。

形式:
    {
      "input": [
        {
          "content": [
            { "type": "image", "format": "base64", "value": "<base64>" }
          ]
        }
      ]
    }

判定: 違う2画像のembeddingが cosine < 0.85 になれば「画像として処理されている」=GOOD。

使い方:
    python tools/test_official_format.py <画像1> <画像2>
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
    request_timeout=60,
)

INFERENCE_ID = ".jina-embeddings-v5-omni-small"


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def extract_emb(resp):
    for key in ("embeddings", "text_embedding", "embedding"):
        if key in resp and len(resp[key]) > 0:
            first = resp[key][0]
            return first["embedding"] if isinstance(first, dict) else first
    raise ValueError(f"unknown keys: {list(resp.keys())}")


# ============================================================
# 公式の content block 形式で画像を渡す関数
# ============================================================
def embed_image_official(image_path):
    """
    画像ファイルを base64 にエンコードし、公式の content block 形式で
    Elastic の _inference API に投げる。

    重要なポイント (公式ドキュメントから):
      - content は配列ではなく単一オブジェクト
      - value は data URI prefix 込み (data:image/jpeg;base64,...)
    """
    b64 = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    data_uri = f"data:image/jpeg;base64,{b64}"
    resp = es.inference.inference(
        inference_id=INFERENCE_ID,
        input=[
            {
                "content": {
                    "type": "image",
                    "format": "base64",
                    "value": data_uri,
                }
            }
        ],
    )
    return extract_emb(resp)


# テキスト embedding 用 (動作確認のため)
def embed_text(text):
    resp = es.inference.inference(inference_id=INFERENCE_ID, input=[text])
    return extract_emb(resp)


# ============================================================
# テスト実行
# ============================================================
if len(sys.argv) < 3:
    print("使い方: python tools/test_official_format.py <画像1> <画像2>")
    sys.exit(1)

p1, p2 = Path(sys.argv[1]), Path(sys.argv[2])

print("============================================================")
print("  Elastic 公式の content block 形式テスト")
print("============================================================\n")
print(f"画像1: {p1.name}")
print(f"画像2: {p2.name}\n")

try:
    emb1 = embed_image_official(p1)
    emb2 = embed_image_official(p2)
    print(f"✅ API コール成功 (次元: {len(emb1)})")

    sim = cosine(emb1, emb2)
    print(f"\n画像1 vs 画像2 の cosine 類似度: {sim:.4f}")

    if sim < 0.85:
        print("✅ 画像として正しく処理されている (違う画像 = 違う embedding)\n")

        # おまけ: テキストとの cross-modal アライメントを確認
        sea_emb = embed_text("sea")
        sim_text_p1 = cosine(sea_emb, emb1)
        sim_text_p2 = cosine(sea_emb, emb2)
        print(f"テキスト 'sea' と画像1: {sim_text_p1:.4f}")
        print(f"テキスト 'sea' と画像2: {sim_text_p2:.4f}")
        print("\n→ この形式を Phase 3 に取り込んで再 ingest しましょう。")
    else:
        print("❌ まだ似すぎている — この形式でも画像として読まれていない")

except Exception as e:
    print(f"❌ エラー: {e}")
