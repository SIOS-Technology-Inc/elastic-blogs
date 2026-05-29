"""
Phase 1: S3 バケットを作成し、セキュリティ設定を行うスクリプト

このスクリプトが何をするか:
  1. .env から AWS の接続情報を読み込む
  2. バケットが存在しなければ作る (既にあればスキップ)
  3. パブリックアクセスを4つの設定すべてで遮断する
  4. SSE-S3 (AES-256) で暗号化を有効化する
  5. バージョニングを有効化する (誤削除対策)
  6. 設定が正しく反映されたか最終確認する

重要: バケットポリシー (put_bucket_policy) は一切設定しない。
      IAM ユーザーの権限 + 上の3つのバケット設定だけで運用する。

使い方:
    source venv/bin/activate
    python setup/create_s3_bucket.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError


# ============================================================
# ステップ 1: .env から接続情報を読み込む
# ============================================================
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
AWS_REGION = os.environ.get("AWS_REGION", "").strip()
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "").strip()

# どれか1つでも空ならエラーで止める
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME]):
    print("❌ .env の AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION / S3_BUCKET_NAME のどれかが未設定です。")
    sys.exit(1)

print("============================================================")
print("  Phase 1: S3 バケット設定")
print("============================================================\n")
print(f"📦 バケット名: {S3_BUCKET_NAME}")
print(f"🌏 リージョン: {AWS_REGION}\n")


# ============================================================
# ステップ 2: S3 クライアントを作る
# ============================================================
# boto3.client() は接続情報を渡してクライアントを返すだけ。
# 実際の通信はメソッドを呼んだ瞬間に発生する。
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


# ============================================================
# ステップ 3: バケットの存在確認 → 必要なら作成
# ============================================================
# head_bucket は「バケットがあるか?」をチェックするだけのメソッド。
# 存在しなければ ClientError (404) が返ってくる。
print("▶ バケットの存在を確認しています...")
try:
    s3.head_bucket(Bucket=S3_BUCKET_NAME)
    print(f"✅ バケット '{S3_BUCKET_NAME}' は既に存在します (このアカウント所有)\n")
except ClientError as e:
    code = e.response["Error"]["Code"]

    # 他人のアカウントがこの名前を使っている (バケット名は AWS 全体で一意)
    if code in ("403", "Forbidden"):
        print(f"❌ バケット名 '{S3_BUCKET_NAME}' は他の AWS アカウントが既に使っています。")
        print("   .env の S3_BUCKET_NAME を別の名前に変えてください (例: image-search-poc-<your-initials>-<yyyymmdd>)。")
        sys.exit(1)

    # 存在しないので新規作成する
    print(f"▶ バケット '{S3_BUCKET_NAME}' を作成しています...")
    try:
        # us-east-1 以外のリージョンでは LocationConstraint が必須
        if AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            s3.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )
        print(f"✅ バケット '{S3_BUCKET_NAME}' を作成しました\n")
    except ClientError as create_err:
        create_code = create_err.response["Error"]["Code"]
        if create_code in ("AccessDenied", "AccessDeniedException"):
            print("❌ アクセス拒否: IAM ユーザーに `s3:CreateBucket` 権限が無いようです。")
            print("")
            print("   対処方法 (どちらかを選んでください):")
            print("   ─────────────────────────────────────────────")
            print("   A) AWS コンソールから手動でバケットを作成する (おすすめ)")
            print("      1. https://s3.console.aws.amazon.com/s3/buckets を開く")
            print(f"      2. 「Create bucket」 → Bucket name に '{S3_BUCKET_NAME}'")
            print(f"      3. Region に '{AWS_REGION}'")
            print("      4. 「Block all public access」 ON のまま 「Create bucket」")
            print("      5. もう一度このスクリプトを実行する")
            print("")
            print("   B) IAM ユーザーに一時的に s3:CreateBucket 権限を付与する")
            sys.exit(1)
        print(f"❌ バケット作成に失敗しました ({create_code}): {create_err}")
        sys.exit(1)


# ============================================================
# ステップ 4: パブリックアクセスを完全に遮断
# ============================================================
# 4つの設定すべてを True にして、どんな経路でもパブリックにできないようにする。
print("▶ パブリックアクセスを遮断しています...")
try:
    s3.put_public_access_block(
        Bucket=S3_BUCKET_NAME,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )
    print("✅ パブリックアクセスを遮断しました (4つの設定すべて有効)\n")
except ClientError as e:
    print(f"❌ パブリックアクセス遮断に失敗 ({e.response['Error']['Code']}): {e}")
    print("   IAM ユーザーに `s3:PutBucketPublicAccessBlock` 権限を付与してください。")
    sys.exit(1)


# ============================================================
# ステップ 5: サーバーサイド暗号化 (SSE-S3 / AES256) を有効化
# ============================================================
# 保存される全オブジェクトを AWS 管理の鍵で自動暗号化する (一番安いオプション)。
print("▶ 暗号化 (SSE-S3 / AES256) を有効化しています...")
try:
    s3.put_bucket_encryption(
        Bucket=S3_BUCKET_NAME,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
            ]
        },
    )
    print("✅ 暗号化を有効化しました (AES-256)\n")
except ClientError as e:
    print(f"❌ 暗号化設定に失敗 ({e.response['Error']['Code']}): {e}")
    print("   IAM ユーザーに `s3:PutEncryptionConfiguration` 権限を付与してください。")
    sys.exit(1)


# ============================================================
# ステップ 6: バージョニングを有効化
# ============================================================
# 誤って上書き・削除しても古いバージョンが残るようにする。
print("▶ バージョニングを有効化しています...")
try:
    s3.put_bucket_versioning(
        Bucket=S3_BUCKET_NAME,
        VersioningConfiguration={"Status": "Enabled"},
    )
    print("✅ バージョニングを有効化しました\n")
except ClientError as e:
    print(f"❌ バージョニング設定に失敗 ({e.response['Error']['Code']}): {e}")
    print("   IAM ユーザーに `s3:PutBucketVersioning` 権限を付与してください。")
    sys.exit(1)


# ============================================================
# ステップ 7: 最終確認 (設定を読み返して表示)
# ============================================================
print("▶ 最終確認:")

# パブリックアクセス遮断の確認
pab = s3.get_public_access_block(Bucket=S3_BUCKET_NAME)["PublicAccessBlockConfiguration"]
all_blocked = all([pab["BlockPublicAcls"], pab["IgnorePublicAcls"], pab["BlockPublicPolicy"], pab["RestrictPublicBuckets"]])
print(f"  {'✅' if all_blocked else '❌'} パブリックアクセス遮断: {'全項目ON' if all_blocked else '一部未設定'}")

# 暗号化の確認
enc = s3.get_bucket_encryption(Bucket=S3_BUCKET_NAME)["ServerSideEncryptionConfiguration"]["Rules"][0]
algo = enc["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]
print(f"  ✅ 暗号化アルゴリズム: {algo}")

# バージョニングの確認
ver = s3.get_bucket_versioning(Bucket=S3_BUCKET_NAME).get("Status", "未設定")
print(f"  {'✅' if ver == 'Enabled' else '❌'} バージョニング: {ver}")

print("\n🎉 Phase 1 完了！次は Phase 2 (Elastic インデックスの作成) に進めます。")
