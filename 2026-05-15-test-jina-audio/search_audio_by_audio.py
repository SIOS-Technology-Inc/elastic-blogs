import base64
import json
import os
import subprocess
from pathlib import Path


def load_dotenv(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        os.environ.setdefault(key, value)


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"環境変数 {name} が設定されていません。")
    return value


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio-samples"

ES_URL = require_env("ES_URL")
ES_USER = require_env("ES_USER")
ELASTIC_PASSWORD = require_env("ELASTIC_PASSWORD")
INDEX_NAME = require_env("INDEX_NAME")
INFERENCE_ID = require_env("INFERENCE_ID")


def run_curl(method, url, body_file=None):
    command = [
        "curl",
        "-s",
        "-k",
        "-u",
        f"{ES_USER}:{ELASTIC_PASSWORD}",
        "-X",
        method,
        url,
        "-H",
        "Accept: application/json",
        "-H",
        "Content-Type: application/json",
    ]

    if body_file:
        command.extend(["--data-binary", f"@{body_file}"])

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return json.loads(result.stdout)


def audio_to_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_audio_embedding(file_name):
    file_path = AUDIO_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    audio_b64 = audio_to_base64(file_path)
    audio_input = f"data:audio/wav;base64,{audio_b64}"

    request_body = {
        "input": [audio_input]
    }

    request_file = Path("audio_query_embedding_request.json")
    request_file.write_text(json.dumps(request_body), encoding="utf-8")

    response = run_curl(
        "POST",
        f"{ES_URL}/_inference/embedding/{INFERENCE_ID}",
        request_file
    )

    embedding = response["embeddings"][0]["embedding"]

    print("Audio query embedding dim:", len(embedding))
    print("Audio query embedding first 5:", embedding[:5])

    return embedding


def search_by_audio(file_name):
    query_vector = create_audio_embedding(file_name)

    search_body = {
        "knn": {
            "field": "embedding",
            "query_vector": query_vector,
            "k": 5,
            "num_candidates": 10
        },
        "_source": [
            "audio_id",
            "file_name",
            "expected_topic",
            "audio_url"
        ]
    }

    search_file = Path("audio_to_audio_search_request.json")
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

    file_name = input("Enter audio file name, example 1.wav: ")

    response = search_by_audio(file_name)

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