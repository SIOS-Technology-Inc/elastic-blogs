import base64
import os
from datetime import datetime, timezone
from pathlib import Path

from elasticsearch import Elasticsearch


# ---------------------------------------
# .env loader (no external library)
# ---------------------------------------

def load_dotenv(path: str = ".env") -> None:
    """KEY=VALUE 形式の .env を読み込み、os.environ にセットする。
    既に環境変数がある場合は上書きしない（シェル指定を優先）。
    """
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def require_env(name: str) -> str:
    """必須の環境変数を読み込む。なければ起動時にエラーで止める。"""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"環境変数 {name} が設定されていません。.env ファイルを確認してください。"
        )
    return value


# ---------------------------------------
# Basic settings
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio-samples"

# .env を読み込み
load_dotenv(BASE_DIR / ".env")

# Elasticsearch 接続情報（.env から読む）
ES_URL = require_env("ES_URL")
ES_USER = require_env("ES_USER")
ES_PASSWORD = require_env("ELASTIC_PASSWORD")

INDEX_NAME = "audio-poc-jina-eis-v1"
INFERENCE_ID = ".jina-embeddings-v5-omni-small"


# ---------------------------------------
# Elasticsearch client
# ---------------------------------------

es = Elasticsearch(
    ES_URL,
    basic_auth=(ES_USER, ES_PASSWORD),
    verify_certs=False
)


# ---------------------------------------
# Audio metadata
# ---------------------------------------

audio_docs = [
    {
        "audio_id": "audio-001",
        "file_name": "1.wav",
        "expected_topic": "ログインできない",
        "audio_url": ""
    },
    {
        "audio_id": "audio-002",
        "file_name": "2.wav",
        "expected_topic": "パスワード再設定",
        "audio_url": ""
    },
    {
        "audio_id": "audio-003",
        "file_name": "3.wav",
        "expected_topic": "クレジットカード決済エラー",
        "audio_url": ""
    },
    {
        "audio_id": "audio-004",
        "file_name": "4.wav",
        "expected_topic": "サービス画面のフリーズ",
        "audio_url": ""
    },
    {
        "audio_id": "audio-005",
        "file_name": "5.wav",
        "expected_topic": "契約プランと請求金額の確認",
        "audio_url": ""
    }
]


# ---------------------------------------
# Helper functions
# ---------------------------------------

def audio_to_base64(file_path: Path) -> str:
    """Read an audio file and convert it to a Base64 string."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_audio_embedding(file_path: Path) -> list:
    """Send Base64 audio to Elastic inference endpoint and get embedding."""
    audio_b64 = audio_to_base64(file_path)

    # data URI プレフィックスを付けて「音声データ」だとモデルに伝える
    audio_input = f"data:audio/wav;base64,{audio_b64}"

    # Accept と Content-Type は両方指定する必要がある
    # （片方だけだと互換バージョンと衝突して 400 エラーになる）
    response = es.perform_request(
        "POST",
        f"/_inference/embedding/{INFERENCE_ID}",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body={
            "input": [audio_input]
        }
    )

    return response["embeddings"][0]["embedding"]


# ---------------------------------------
# Main process
# ---------------------------------------

def main():
    print(f"Audio directory: {AUDIO_DIR}")

    for doc in audio_docs:
        file_path = AUDIO_DIR / doc["file_name"]

        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        print(f"Processing {file_path}...")

        embedding = get_audio_embedding(file_path)

        indexed_doc = {
            "audio_id": doc["audio_id"],
            "file_name": doc["file_name"],
            "expected_topic": doc["expected_topic"],
            "audio_url": doc["audio_url"],
            "embedding": embedding,
            "embedding_method": "elastic_inference_jina_omni_small",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        es.index(
            index=INDEX_NAME,
            id=doc["audio_id"],
            document=indexed_doc
        )

        print(
            f"Indexed {doc['file_name']} "
            f"with embedding dimension {len(embedding)}"
        )

    print("Done.")


if __name__ == "__main__":
    main()