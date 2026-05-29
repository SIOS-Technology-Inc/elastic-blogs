"""
画像入力フォーマットの実験スクリプト

Phase 3 で使ったフォーマット (URL を文字列として渡す) は、Jina v5 omni に
テキストとして扱われていることが判明した。

このスクリプトは複数の入力フォーマットを試して、どれが「画像として」処理されるかを確認する。
判定基準: 違う2つの画像を渡したとき、embedding のコサイン類似度が 0.85 未満になれば
         画像として処理されている (= 違う画像は違うベクトルになる)。

使い方:
    python tools/test_image_formats.py <画像1のパス> <画像2のパス>
    例: python tools/test_image_formats.py \\
          /Users/.../poc-images/IMG_8133.jpeg \\
          /Users/.../poc-images/IMG_8851.jpeg
"""

import base64
import math
import os
import sys
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

INFERENCE_ID = ".jina-embeddings-v5-omni-small"


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def get_embedding_from_response(response):
    for key in ("embeddings", "text_embedding", "embedding"):
        if key in response and len(response[key]) > 0:
            first = response[key][0]
            return first["embedding"] if isinstance(first, dict) else first
    raise ValueError(f"embedding が見つからない。キー: {list(response.keys())}")


# ============================================================
# 引数チェック
# ============================================================
if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

image1_path = Path(sys.argv[1])
image2_path = Path(sys.argv[2])

if not image1_path.is_file() or not image2_path.is_file():
    print(f"❌ 画像ファイルが見つかりません")
    sys.exit(1)

# 画像をバイナリ → base64 に変換
b64_1 = base64.b64encode(image1_path.read_bytes()).decode("ascii")
b64_2 = base64.b64encode(image2_path.read_bytes()).decode("ascii")

print(f"画像1: {image1_path.name} ({len(b64_1)} chars base64)")
print(f"画像2: {image2_path.name} ({len(b64_2)} chars base64)\n")


# ============================================================
# 試すフォーマット一覧
# ============================================================
# 各フォーマットは「画像1用と画像2用のペイロード」を返す関数として定義
formats = [
    (
        "1. data URI 形式 (data:image/jpeg;base64,...)",
        lambda b1, b2: ([f"data:image/jpeg;base64,{b1}"], [f"data:image/jpeg;base64,{b2}"]),
    ),
    (
        "2. 純粋な base64 文字列",
        lambda b1, b2: ([b1], [b2]),
    ),
    (
        "3. dict 形式 {'image': data_uri}",
        lambda b1, b2: ([{"image": f"data:image/jpeg;base64,{b1}"}], [{"image": f"data:image/jpeg;base64,{b2}"}]),
    ),
    (
        "4. OpenAI 互換 {'type':'image_url','image_url':{'url':...}}",
        lambda b1, b2: (
            [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b1}"}}],
            [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b2}"}}],
        ),
    ),
]


# ============================================================
# 各フォーマットを試す
# ============================================================
results = []

for name, builder in formats:
    print(f"▶ {name}")
    input1, input2 = builder(b64_1, b64_2)
    try:
        resp1 = es.inference.inference(inference_id=INFERENCE_ID, input=input1)
        emb1 = get_embedding_from_response(resp1)
        resp2 = es.inference.inference(inference_id=INFERENCE_ID, input=input2)
        emb2 = get_embedding_from_response(resp2)
        sim = cosine(emb1, emb2)
        verdict = "✅ OK (画像として処理されている)" if sim < 0.85 else "❌ NG (まだテキスト扱い)"
        print(f"   類似度 = {sim:.4f}   {verdict}\n")
        results.append((name, sim, None))
    except Exception as e:
        print(f"   ❌ API エラー: {str(e)[:200]}\n")
        results.append((name, None, str(e)[:200]))


# ============================================================
# 結論
# ============================================================
print("============================================================")
print("  サマリー")
print("============================================================")
working = [(name, sim) for name, sim, err in results if sim is not None and sim < 0.85]
if working:
    print("✅ 動くフォーマットが見つかった:")
    for name, sim in working:
        print(f"   - {name}  (sim={sim:.4f})")
    print("\n→ Phase 3 のスクリプトをこのフォーマットで書き換えて再 ingest します。")
else:
    print("❌ どのフォーマットでも画像として処理されなかった。")
    print("   別のアプローチが必要 (例: 別の inference モデル、task_settings、など)。")
