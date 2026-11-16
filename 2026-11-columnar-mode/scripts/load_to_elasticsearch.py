#!/usr/bin/env python3
"""
access_logs.ndjson を Elasticsearch の Bulk API で投入するスクリプト（外部ライブラリ不要）

使い方の例:
  # APIキー認証（Elastic Cloud / Serverless）
  python3 load_to_elasticsearch.py --url https://xxx.es.cloud:443 --api-key "xxxx" --index access-logs-columnar

  # Basic認証（ローカルなど）
  python3 load_to_elasticsearch.py --url http://localhost:9200 --user elastic --password changeme --index access-logs-standard

  # 件数を絞って試す
  python3 load_to_elasticsearch.py ... --limit 10000

注意: index は事前に作成しておくこと（index.mode を変えて比較するため）。
"""
import argparse
import os
import base64
import json
import ssl
import sys
import time
import urllib.request


def load_dotenv():
    """スクリプトと同じフォルダの .env を読んで環境変数に入れる (外部ライブラリ不要)"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ[key] = value  # .env の値を優先する

def post_bulk(url, headers, body, insecure):
    req = urllib.request.Request(url + "/_bulk", data=body.encode("utf-8"), headers=headers, method="POST")
    ctx = ssl._create_unverified_context() if insecure else None
    with urllib.request.urlopen(req, context=ctx, timeout=120) as res:
        return json.loads(res.read())


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("ES_URL"), help="例: http://localhost:9200 (環境変数 ES_URL でも可)")
    ap.add_argument("--index", required=True, help="投入先 index 名")
    ap.add_argument("--file", default="access_logs.ndjson")
    ap.add_argument("--api-key", default=os.environ.get("ES_API_KEY"), help="APIキー (Kibana が出す encoded 値)")
    ap.add_argument("--user")
    ap.add_argument("--password")
    ap.add_argument("--batch", type=int, default=5000, help="1回の bulk に入れる件数")
    ap.add_argument("--limit", type=int, default=0, help="投入する最大件数 (0 = 全件)")
    ap.add_argument("--insecure", action="store_true", default=os.environ.get("ES_INSECURE") == "1", help="TLS証明書を検証しない (環境変数 ES_INSECURE=1 でも可)")
    args = ap.parse_args()
    if not args.url:
        ap.error("--url か環境変数 ES_URL を指定してください")
    if not args.user and not args.api_key and os.environ.get("ES_AUTH"):
        args.user, _, args.password = os.environ["ES_AUTH"].partition(":")

    headers = {"Content-Type": "application/x-ndjson"}
    if args.api_key:
        headers["Authorization"] = "ApiKey " + args.api_key
    elif args.user:
        token = base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
        headers["Authorization"] = "Basic " + token

    action = json.dumps({"index": {"_index": args.index}}) + "\n"
    buf = []
    sent = 0
    errors = 0
    t0 = time.time()

    def flush():
        nonlocal sent, errors
        if not buf:
            return
        res = post_bulk(args.url, headers, "".join(buf), args.insecure)
        if res.get("errors"):
            for item in res["items"]:
                err = item.get("index", {}).get("error")
                if err:
                    errors += 1
                    if errors <= 3:
                        print("ERROR:", json.dumps(err)[:300], file=sys.stderr)
        sent += len(buf) // 2
        buf.clear()
        print(f"  sent {sent:,} docs  ({time.time() - t0:.0f}s)", flush=True)

    with open(args.file, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if args.limit and i >= args.limit:
                break
            buf.append(action)
            buf.append(line if line.endswith("\n") else line + "\n")
            if len(buf) >= args.batch * 2:
                flush()
        flush()

    elapsed = time.time() - t0
    print(f"done: {sent:,} docs, {errors} errors, {elapsed:.1f}s, {sent / elapsed:,.0f} docs/sec")


if __name__ == "__main__":
    main()
