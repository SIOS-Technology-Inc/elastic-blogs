"""
Phase 3: 画像を S3 にアップロード → 埋め込みを取得 → Elastic に登録

各画像について:
  1. S3 にアップロード (poc-uploads/<filename>) — 後で Agent Builder で表示する用
  2. ローカルのファイルを base64 にエンコードして data URI 形式の文字列にする
  3. Jina v5 omni の _inference を「公式 content block 形式」で呼ぶ:
       {"content": {"type": "image", "format": "base64", "value": "data:..."}}
     これで初めて画像として扱われる (URL や生 base64 文字列は test 扱い)
  4. 返ってきた 1024 次元ベクトルを image_embedding として alias に登録

何度実行しても安全 (idempotent):
  - S3 は同じキーがあれば上書き
  - Elastic は image_key を _id として使うので、同じ画像は1ドキュメントに保たれる

使い方:
    source venv/bin/activate
    python ingest/upload_and_index.py /path/to/poc-images
"""

import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import boto3
from elasticsearch import Elasticsearch


# ============================================================
# ステップ 1: コマンドライン引数からフォルダパスを取得
# ============================================================
if len(sys.argv) < 2:
    print("❌ 使い方: python ingest/upload_and_index.py <画像フォルダのパス>")
    sys.exit(1)

image_folder = Path(sys.argv[1]).expanduser().resolve()

if not image_folder.is_dir():
    print(f"❌ '{image_folder}' はフォルダではないか、存在しません。")
    sys.exit(1)


# ============================================================
# ステップ 2: .env から接続情報を読み込む
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
INDEX_NAME = os.environ["INDEX_NAME"].strip()  # alias 名

INFERENCE_ID = ".jina-embeddings-v5-omni-small"


# ============================================================
# ステップ 3: フォルダ内の画像ファイル一覧
# ============================================================
extensions = {".jpg", ".jpeg", ".png"}
image_files = sorted([
    f for f in image_folder.iterdir()
    if f.is_file() and f.suffix.lower() in extensions
])

if not image_files:
    print(f"❌ '{image_folder}' に .jpg / .jpeg / .png ファイルがありません。")
    sys.exit(1)

total = len(image_files)

print("============================================================")
print("  Phase 3: 画像のアップロードと埋め込み生成・登録")
print("============================================================\n")
print(f"📁 フォルダ:           {image_folder}")
print(f"🖼  対象画像ファイル数: {total}")
print(f"📦 S3:                 {S3_BUCKET_NAME}/{S3_UPLOAD_PREFIX}/")
print(f"📚 Elastic alias:      {INDEX_NAME}\n")


# ============================================================
# ステップ 4: クライアントを作る
# ============================================================
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# request_timeout を長めに: 推論の初回はモデルウォームアップで時間がかかる
es = Elasticsearch(
    hosts=[ELASTIC_URL],
    api_key=ELASTIC_API_KEY,
    request_timeout=300,
)


# ============================================================
# ステップ 5: 各画像をループ処理
# ============================================================
success_count = 0
failed_files = []

for i, image_path in enumerate(image_files, start=1):
    filename = image_path.name
    image_key = f"{S3_UPLOAD_PREFIX}/{filename}"

    print(f"[{i}/{total}] {filename}")

    try:
        # ----- 5-1. S3 にアップロード (Agent Builder で表示する用) -----
        s3.upload_file(str(image_path), S3_BUCKET_NAME, image_key)
        print("   ✅ S3 アップロード完了")

        # ----- 5-2. ローカルのファイルを base64 にエンコード -----
        # 拡張子から MIME タイプを判定する。Jina API は内容 (magic bytes) でも形式を
        # 判定してくれるが、仕様的には data URI の MIME とバイナリは一致させるべき。
        image_bytes = image_path.read_bytes()
        b64 = base64.b64encode(image_bytes).decode("ascii")
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }.get(image_path.suffix.lower(), "image/jpeg")
        data_uri = f"data:{mime};base64,{b64}"

        # ----- 5-3. 公式の content block 形式で Jina v5 omni を呼ぶ -----
        # 重要: content は単一オブジェクト (配列ではない)、value は data URI prefix 付き
        # このフォーマットでしか「画像として」処理されない (URL/生base64は text 扱い)
        response = es.inference.inference(
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

        # レスポンスから embedding を取り出す (キー名はバージョンで変わるので複数試す)
        embedding = None
        for key in ("embeddings", "text_embedding", "embedding"):
            if key in response and len(response[key]) > 0:
                first = response[key][0]
                embedding = first["embedding"] if isinstance(first, dict) else first
                break
        if embedding is None:
            raise ValueError(
                f"埋め込みが見つかりません。レスポンスのキー: {list(response.keys())}"
            )
        print(f"   ✅ 埋め込み取得完了 ({len(embedding)} 次元)")

        # ----- 5-4. ドキュメントを alias に登録 -----
        # id=image_key にすることで、同じ画像を再 ingest しても重複しない
        es.index(
            index=INDEX_NAME,
            id=image_key,
            document={
                "image_key": image_key,
                "name": image_path.stem,
                "image_embedding": embedding,
            },
            refresh="wait_for",
        )
        print("   ✅ Elastic 登録完了\n")
        success_count += 1

    except Exception as e:
        print(f"   ❌ 失敗: {e}\n")
        failed_files.append((filename, str(e)))


# ============================================================
# ステップ 6: サマリー
# ============================================================
print("============================================================")
print(f"📊 結果: {success_count}/{total} 件成功")
print("============================================================")

if failed_files:
    print(f"\n❌ 失敗したファイル ({len(failed_files)} 件):")
    for fname, err in failed_files:
        print(f"  - {fname}: {err[:120]}")

if success_count == total:
    print("\n🎉 Phase 3 完了！次は Phase 4 (検索ツール) に進めます。")
elif success_count > 0:
    print("\n⚠️  一部のファイルが失敗しました。")
else:
    print("\n❌ 全ファイル失敗。")
    sys.exit(1)
