"""
Phase 4 (改良版): kNN + query_vector_builder で検索する

旧バージョンとの違い:
  - 旧: Python 側で _inference を呼んでベクトルを作り、それを query_vector に渡す
  - 新: 1回の _search リクエストの中で Elastic が _inference を呼んでくれる
        → Python 側は inference を意識しなくていい
        → Agent Builder の Search Template でも同じことが直接書ける

実装:
  - search_by_text:        query_vector_builder.embedding (text input)
  - search_by_text_in_image: query_vector_builder.embedding (text input, agent が prompt 整形)
  - search_by_filename:    query_vector_builder.lookup (別 doc の embedding を取り出して query に使う)

使い方:
  python tools/search_tools.py text "タクシー"
  python tools/search_tools.py filename "IMG_8133.jpeg"
  python tools/search_tools.py text_in_image "SOLD"
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import boto3
from elasticsearch import Elasticsearch


# ============================================================
# 設定 — .env を読み込んでクライアントを準備
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
# ヘルパー
# ============================================================

# S3 オブジェクトキー → 1時間有効の pre-signed URL に変換
def make_presigned_url(image_key):
    """
    S3 の pre-signed URL を作る。

    ResponseContentType を付ける理由:
      boto3 の upload_file() は ContentType メタデータを自動で付けないことがあり、
      ブラウザがファイルをダウンロードしてしまう (inline 表示できない)。
      pre-signed URL に response-content-type を指定すると、S3 が応答時に
      その Content-Type ヘッダを返してくれる → ブラウザが画像として描画する。
    """
    # 拡張子から MIME type を判定
    ext = Path(image_key).suffix.lower()
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(ext, "image/jpeg")

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key": image_key,
            "ResponseContentType": content_type,
        },
        # ExpiresIn=600 (10分): チャットの画像リンクが screenshot で漏れた場合の
        # 露出時間を短くする。クリックして開くには十分。
        ExpiresIn=600,
    )


# 検索結果を整形する (hits → [{name, score, image_url}])
def format_hits(hits):
    return [
        {
            "name": h["_source"]["name"],
            "score": f"{min(h['_score'] * 100, 100):.2f}%",
            "image_url": make_presigned_url(h["_source"]["image_key"]),
        }
        for h in hits
    ]


# ============================================================
# Tool 1: 自然言語で画像を検索
# ============================================================
def search_by_text(query: str) -> list:
    """
    例: 'タクシー', 'red sports car', 'グループディスカッション'

    kNN + query_vector_builder.embedding を使う。
    Elastic がリクエストの中で _inference を呼んで text → vector に変換し、
    image_embedding フィールドに対する kNN 検索まで一気に行う。
    """
    result = es.search(
        index=INDEX_NAME,
        query={
            "knn": {
                "field": "image_embedding",
                "k": 3,
                "num_candidates": 50,
                "query_vector_builder": {
                    "embedding": {
                        "inference_id": INFERENCE_ID,
                        "input": {"type": "text", "value": query},
                    }
                },
            }
        },
        size=3,
        source=["image_key", "name"],
    )
    return format_hits(result["hits"]["hits"])


# ============================================================
# Tool 2: 既存ファイル名から似た画像を検索
# ============================================================
def search_by_filename(filename: str) -> list:
    """
    例: 'IMG_8133.jpeg' → 視覚的に似た画像 上位3件

    kNN + query_vector_builder.lookup を使う。
    Elastic が指定の doc の image_embedding を取ってきて、それを query_vector として
    使う。自分自身は除外。
    """
    image_key = f"{S3_UPLOAD_PREFIX}/{filename}"

    # 自分が存在しないとエラーで止まるので事前確認
    if not es.exists(index=INDEX_NAME, id=image_key):
        print(f"⚠️  '{filename}' はインデックスに見つかりませんでした")
        return []

    result = es.search(
        index=INDEX_NAME,
        # k=4 で取って、自分自身を除いて上位3件に絞る
        query={
            "bool": {
                "must_not": [{"term": {"image_key": image_key}}],
                "must": [
                    {
                        "knn": {
                            "field": "image_embedding",
                            "k": 4,
                            "num_candidates": 50,
                            "query_vector_builder": {
                                "lookup": {
                                    "index": INDEX_NAME,
                                    "id": image_key,
                                    "path": "image_embedding",
                                }
                            },
                        }
                    }
                ],
            }
        },
        size=3,
        source=["image_key", "name"],
    )
    return format_hits(result["hits"]["hits"])


# ============================================================
# Tool 3: 画像に書かれている文字で検索
# ============================================================
def search_by_text_in_image(visible_text: str) -> list:
    """
    例: 'SOLD' → 'SOLD' が画像に写っている画像 上位3件
    Jina v5 omni は multimodal なので、画像内の文字もテキストプロンプトで近づけられる。
    プロンプトを工夫して「画像にこの文字が見える」という意味にする。
    """
    prompt = f"an image containing the visible text '{visible_text}'"
    return search_by_text(prompt)  # Tool 1 をそのまま再利用


# ============================================================
# CLI でローカルテスト
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使い方:")
        print('  python tools/search_tools.py text "タクシー"')
        print('  python tools/search_tools.py filename "IMG_8133.jpeg"')
        print('  python tools/search_tools.py text_in_image "SOLD"')
        sys.exit(1)

    mode = sys.argv[1]
    query = sys.argv[2]

    print(f"🔍 検索モード: {mode}")
    print(f"📝 クエリ:    {query}\n")

    if mode == "text":
        results = search_by_text(query)
    elif mode == "filename":
        results = search_by_filename(query)
    elif mode == "text_in_image":
        results = search_by_text_in_image(query)
    else:
        print(f"❌ 不明なモード: '{mode}'")
        print("   有効: text / filename / text_in_image")
        sys.exit(1)

    if not results:
        print("結果: 0件")
    else:
        print(f"📊 上位 {len(results)} 件の結果:\n")
        for i, r in enumerate(results, start=1):
            print(f"  [{i}] {r['name']}  (類似度: {r['score']})")
            print(f"      URL: {r['image_url']}")
            print()
