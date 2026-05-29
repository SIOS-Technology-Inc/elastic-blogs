"""
診断スクリプト: 画像の埋め込みが正しく生成されているかチェックする

このスクリプトは以下の3つの比較を行う:
  比較A: 異なる2画像の保存済み embedding 同士のコサイン類似度
         → 高すぎる(>0.95)なら、全画像が同じような embedding になっている (BAD)
         → 低い(<0.7)なら、画像ごとに違う embedding になっている (GOOD)

  比較B: 「画像URL」を渡した結果の embedding と
         「画像URLと似たテキスト文字列」を渡した結果の embedding
         → 非常に近い(>0.9)なら、URL がテキストとして埋め込まれている (BAD)

  比較C: 文字列 "sea" の embedding と各画像の embedding
         → 画像内容が反映されていれば、海の画像で高く、それ以外で低くなる

実行:
  python tools/diagnose_embeddings.py
"""

import math
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import boto3
from elasticsearch import Elasticsearch


# ============================================================
# 共通設定
# ============================================================
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

ELASTIC_URL = os.environ["ELASTIC_URL"].strip()
ELASTIC_API_KEY = os.environ["ELASTIC_API_KEY"].strip()
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"].strip()
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"].strip()
AWS_REGION = os.environ["AWS_REGION"].strip()
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"].strip()
S3_UPLOAD_PREFIX = os.environ["S3_UPLOAD_PREFIX"].strip()
INDEX_NAME = os.environ["INDEX_NAME"].strip()
INFERENCE_ID = ".jina-embeddings-v5-omni-small"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

es = Elasticsearch(
    hosts=[ELASTIC_URL],
    api_key=ELASTIC_API_KEY,
    request_timeout=60,
)


# ============================================================
# ヘルパー: cosine類似度を計算する
# ============================================================
def cosine(a, b):
    """2つのベクトルのコサイン類似度を返す (-1〜1)。"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


# ============================================================
# ヘルパー: 入力を Jina v5 omni に渡して埋め込みを取得
# ============================================================
def embed(value):
    response = es.inference.inference(inference_id=INFERENCE_ID, input=[value])
    for key in ("embeddings", "text_embedding", "embedding"):
        if key in response and len(response[key]) > 0:
            first = response[key][0]
            return first["embedding"] if isinstance(first, dict) else first
    raise ValueError(f"embedding が見つからない。キー: {list(response.keys())}")


# ============================================================
# Index から保存済みの画像とその embedding を取り出す
# ============================================================
print("============================================================")
print("  画像埋め込み診断 (Phase 3 の動作確認)")
print("============================================================\n")

# alias から最初の3件を取得 (embedding 付きで)
result = es.search(
    index=INDEX_NAME,
    query={"match_all": {}},
    size=3,
    source=["image_key", "name", "image_embedding"],
)
hits = result["hits"]["hits"]

if len(hits) < 2:
    print(f"❌ インデックスに画像が2件以上ありません ({len(hits)} 件)。")
    sys.exit(1)

img_a = hits[0]["_source"]
img_b = hits[1]["_source"]
key_a = img_a["image_key"]
key_b = img_b["image_key"]
emb_a_stored = img_a["image_embedding"]
emb_b_stored = img_b["image_embedding"]

print(f"対象画像 A: {key_a}")
print(f"対象画像 B: {key_b}\n")


# ============================================================
# 比較A: 別画像の保存済み embedding 同士の類似度
# ============================================================
sim_AB_stored = cosine(emb_a_stored, emb_b_stored)
print(f"【比較A】 保存済みの A と B の embedding コサイン類似度")
print(f"   = {sim_AB_stored:.4f}")
if sim_AB_stored > 0.95:
    print("   ⚠️  非常に高い: 全画像がほぼ同じ embedding になっている可能性 (BAD)")
elif sim_AB_stored > 0.85:
    print("   ⚠️  やや高い: 画像が似ているか、URLがテキストとして埋め込まれている可能性")
else:
    print("   ✅ 画像ごとに違う embedding になっている (GOOD)")
print()


# ============================================================
# 比較B: 画像URL を「画像」として渡したときと、
#       「URLっぽいテキスト」を渡したときの embedding を比較
# ============================================================
# A の S3 オブジェクトキーから pre-signed URL を生成して embedding を取得
presigned_a = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": S3_BUCKET_NAME, "Key": key_a},
    ExpiresIn=3600,
)
emb_url_fresh = embed(presigned_a)

# URLとほぼ同じだが内容が無い文字列 (S3のURLパターン)
fake_url_text = "https://image-search-poc-elastic-saman.s3.amazonaws.com/poc-uploads/fake-file-name.jpg?AWSAccessKeyId=AAA&Signature=BBB&Expires=999"
emb_fake_text = embed(fake_url_text)

sim_url_vs_fake = cosine(emb_url_fresh, emb_fake_text)
print(f"【比較B】 画像URL の embedding と「似たフェイクURL文字列」の embedding")
print(f"   類似度 = {sim_url_vs_fake:.4f}")
if sim_url_vs_fake > 0.9:
    print("   ❌ 非常に近い: URL がテキストとして埋め込まれている (画像内容が無視されている)")
elif sim_url_vs_fake > 0.7:
    print("   ⚠️  かなり近い: URLテキストの影響が強いかも")
else:
    print("   ✅ 十分に違う: 画像URL は画像として正しく処理されている")
print()


# ============================================================
# 比較C: テキストクエリと画像 embedding の類似度
# ============================================================
emb_sea = embed("sea")
emb_taxi = embed("taxi")

sim_sea_A = cosine(emb_sea, emb_a_stored)
sim_sea_B = cosine(emb_sea, emb_b_stored)
sim_taxi_A = cosine(emb_taxi, emb_a_stored)
sim_taxi_B = cosine(emb_taxi, emb_b_stored)

print(f"【比較C】 テキスト 'sea' / 'taxi' と各画像の類似度")
print(f"   'sea'  vs A ({key_a}): {sim_sea_A:.4f}")
print(f"   'sea'  vs B ({key_b}): {sim_sea_B:.4f}")
print(f"   'taxi' vs A ({key_a}): {sim_taxi_A:.4f}")
print(f"   'taxi' vs B ({key_b}): {sim_taxi_B:.4f}")
print()


# ============================================================
# 結論
# ============================================================
print("============================================================")
print("  結論")
print("============================================================")
if sim_url_vs_fake > 0.9 or sim_AB_stored > 0.95:
    print("❌ 画像が画像として処理されていない可能性が高い。")
    print("   Phase 3 のスクリプトを修正して、画像を別の方法で渡す必要がある。")
elif sim_url_vs_fake > 0.7:
    print("⚠️  URL のテキスト的特徴が強く影響している。一部修正が必要かも。")
else:
    print("✅ 画像は画像として正しく埋め込まれている。")
    print("   検索結果が悪いのは、データセットに該当画像が無い・少ないため。")
