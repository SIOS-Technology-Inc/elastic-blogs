import json
print("Running file:", __file__)
import os
import subprocess
from pathlib import Path


def load_dotenv(path=".env"):
    """シンプルな .env ローダー（外部ライブラリ不要）。"""
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


def require_env(name):
    """必須の環境変数を読み込む。なければエラーで止める。"""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"環境変数 {name} が設定されていません。.env を確認してください。"
        )
    return value


# .env を読み込み
load_dotenv()

ES_URL = require_env("ES_URL")
ES_USER = require_env("ES_USER")
ES_PASSWORD_ENV = "ELASTIC_PASSWORD"
require_env(ES_PASSWORD_ENV)
INDEX_NAME = require_env("INDEX_NAME")
INFERENCE_ID = require_env("INFERENCE_ID")


def run_curl(method, url, body_file=None):
    """curl で Elasticsearch にリクエストを送る関数。"""
    password = os.environ[ES_PASSWORD_ENV]

    command = [
        "curl",
        "-s",
        "-k",
        "-u", f"{ES_USER}:{password}",
        "-X", method,
        url,
        "-H", "Content-Type: application/json",
    ]

    if body_file:
        command.extend(["--data-binary", f"@{body_file}"])

    # shell=True は使わずリストで渡す（空白問題を回避）
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"curl 失敗 (code={result.returncode})\n"
            f"stderr: {result.stderr}\nstdout: {result.stdout}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"JSON パース失敗: {e}\nレスポンス本体:\n{result.stdout}"
        )


def create_text_embedding(query_text):
    request_body = {
        "input": [
            query_text
        ]
    }

    request_file = Path("query_embedding_request.json")
    request_file.write_text(json.dumps(request_body), encoding="utf-8")

    response = run_curl(
        "POST",
        f"{ES_URL}/_inference/embedding/{INFERENCE_ID}",
        request_file
    )

    embedding = response["embeddings"][0]["embedding"]

    print("Query embedding dim:", len(embedding))
    print("Query embedding first 5:", embedding[:5])

    if len(embedding) != 1024:
        raise ValueError(f"Unexpected embedding dimension: {len(embedding)}")

    return embedding


def search_audio(query_text):
    query_vector = create_text_embedding(query_text)

    search_body = {
        "knn": {
            "field": "embedding",
            "query_vector": query_vector,
            "k": 3,
            "num_candidates": 10
        },
        "_source": [
            "audio_id",
            "file_name",
            "audio_url",
            "expected_topic"
        ]
    }

    search_file = Path("audio_search_request.json")
    search_file.write_text(json.dumps(search_body), encoding="utf-8")

    response = run_curl(
        "POST",
        f"{ES_URL}/{INDEX_NAME}/_search",
        search_file
    )

    return response


def main():
    print("Using index:", INDEX_NAME)
    print("Using inference endpoint:", INFERENCE_ID)
    query_text = input("Enter Japanese search query: ")

    response = search_audio(query_text)

    print("\nSearch results:")
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        print("-" * 40)
        print("score:", hit["_score"])
        print("file_name:", source["file_name"])
        print("expected_topic:", source["expected_topic"])
        print("audio_url:", source["audio_url"])


if __name__ == "__main__":
    main()
