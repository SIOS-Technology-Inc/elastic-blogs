"""
データセットから画像を削除するスクリプト (S3 と Elastic の両方から)

upload_and_index.py の逆操作。1 ファイルにつき:
  1. Elastic から該当ドキュメントを削除 (_id = image_key)
  2. S3 から該当オブジェクトを削除

両方とも消すことで「片方だけ残るオーファン」を防ぐ。
削除は冪等: 既に無いファイルを指定してもエラーにはしない。

使い方:
    source venv/bin/activate

    # 完全な image_key で指定する場合 (推奨)
    python ingest/delete_images.py poc-uploads/IMG_8687.jpg poc-uploads/IMG_8866.jpeg

    # ファイル名だけでも OK (自動で poc-uploads/ プレフィックスを付ける)
    python ingest/delete_images.py IMG_8687.jpg IMG_8866.jpeg
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import boto3
from elasticsearch import Elasticsearch


# ============================================================
# ステップ 1: コマンドライン引数を受け取る
# ============================================================
if len(sys.argv) < 2:
    print("❌ 使い方: python ingest/delete_images.py <filename1> <filename2> ...")
    print("   例: python ingest/delete_images.py IMG_8687.jpg IMG_8866.jpeg")
    sys.exit(1)

filenames_input = sys.argv[1:]


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
INDEX_NAME = os.environ["INDEX_NAME"].strip()


# ============================================================
# ステップ 3: 入力を image_key に正規化
# ============================================================
# ユーザが "IMG_8687.jpg" だけ入れた場合は "poc-uploads/IMG_8687.jpg" に直す。
# 既に prefix 付きならそのまま使う。
image_keys = []
for name in filenames_input:
    name = name.strip().strip(",")
    if not name:
        continue
    if name.startswith(f"{S3_UPLOAD_PREFIX}/"):
        image_keys.append(name)
    else:
        image_keys.append(f"{S3_UPLOAD_PREFIX}/{name}")

total = len(image_keys)

print("============================================================")
print("  画像をデータセットから削除")
print("============================================================\n")
print(f"📦 S3 バケット:    {S3_BUCKET_NAME}")
print(f"📚 Elastic alias: {INDEX_NAME}")
print(f"🗑  削除対象:      {total} 件\n")
for k in image_keys:
    print(f"  - {k}")
print()


# ============================================================
# ステップ 4: 念のため確認 (誤削除を防ぐため)
# ============================================================
answer = input("本当に削除しますか? (yes と入力): ").strip()
if answer != "yes":
    print("中止しました。")
    sys.exit(0)
print()


# ============================================================
# ステップ 5: クライアント準備
# ============================================================
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

es = Elasticsearch(
    hosts=[ELASTIC_URL],
    api_key=ELASTIC_API_KEY,
    request_timeout=30,
)


# ============================================================
# ステップ 6: 各ファイルを削除 (Elastic → S3 の順)
# ============================================================
# Elastic を先に消す理由: 検索結果に出てくる画像が S3 に無いと壊れて見えるが、
# S3 にあって Elastic に無い状態は単に「未インデックス」で害が少ない。
success_count = 0
failed = []

for i, key in enumerate(image_keys, start=1):
    print(f"[{i}/{total}] {key}")

    # ----- 6-1. Elastic から削除 -----
    try:
        if es.exists(index=INDEX_NAME, id=key):
            es.delete(index=INDEX_NAME, id=key, refresh="wait_for")
            print("   ✅ Elastic から削除")
        else:
            print("   ⏭  Elastic には無し (スキップ)")
    except Exception as e:
        print(f"   ❌ Elastic 削除失敗: {e}")
        failed.append((key, f"elastic: {e}"))
        continue

    # ----- 6-2. S3 から削除 -----
    try:
        # head_object で存在確認 (無ければ ClientError)
        try:
            s3.head_object(Bucket=S3_BUCKET_NAME, Key=key)
            exists_in_s3 = True
        except Exception:
            exists_in_s3 = False

        if exists_in_s3:
            s3.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
            print("   ✅ S3 から削除\n")
        else:
            print("   ⏭  S3 には無し (スキップ)\n")
        success_count += 1
    except Exception as e:
        print(f"   ❌ S3 削除失敗: {e}\n")
        failed.append((key, f"s3: {e}"))


# ============================================================
# ステップ 7: サマリー
# ============================================================
print("============================================================")
print(f"📊 結果: {success_count}/{total} 件削除完了")
print("============================================================")

if failed:
    print(f"\n❌ 失敗 ({len(failed)} 件):")
    for key, err in failed:
        print(f"  - {key}: {err[:120]}")
    sys.exit(1)
