#!/usr/bin/env python3
"""
3つの index (standard / logsdb / columnar) に対してクエリを実行し、結果を表にまとめるスクリプト。
外部ライブラリ不要。

使い方:
  python3 run_benchmark.py --url http://localhost:9200 --user elastic --password changeme
  python3 run_benchmark.py --url https://xxx.es.cloud:443 --api-key "xxxx"

出力: 画面に Markdown の表を表示し、benchmark_result.md にも保存する。
"""
import argparse
import os
import base64
import json
import ssl
import statistics
import time
import urllib.parse
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

INDICES = ["access-logs-standard", "access-logs-logsdb", "access-logs-columnar"]

# ---------- シナリオ3: 集計クエリ ----------
AGG_QUERY = {
    "size": 0,
    "aggs": {
        "by_status": {
            # size を付けないと上位 10 種類しか返らない (ステータスコードは 14 種類)
            "terms": {"field": "http.response.status_code", "size": 20, "order": {"_key": "asc"}},
            "aggs": {"avg_duration": {"avg": {"field": "duration_ms"}}},
        }
    },
}

# ---------- シナリオ4: フィルタクエリ (ソート対象フィールドで絞る = 速いはず) ----------
FILTER_SORTED = {
    "size": 0,
    "track_total_hits": True,
    "query": {
        "bool": {
            "filter": [
                {"term": {"service.name": "order-service"}},
                {"range": {"http.response.status_code": {"gte": 500}}},
                {"range": {"@timestamp": {"gte": "2026-11-06T12:00:00Z", "lt": "2026-11-06T13:00:00Z"}}},
            ]
        }
    },
}

# ---------- シナリオ4': ソート対象でないフィールドで絞る (遅くなるはず) ----------
FILTER_UNSORTED = {
    "size": 0,
    "track_total_hits": True,
    "query": {"bool": {"filter": [{"term": {"url.path": "/api/v1/products/item-9823"}}]}},
}


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("ES_URL"))
    ap.add_argument("--api-key", default=os.environ.get("ES_API_KEY"))
    ap.add_argument("--user")
    ap.add_argument("--password")
    ap.add_argument("--runs", type=int, default=5, help="各クエリの実行回数")
    ap.add_argument("--insecure", action="store_true", default=os.environ.get("ES_INSECURE") == "1")
    ap.add_argument("--out", default="benchmark_result.md")
    args = ap.parse_args()
    if not args.url:
        ap.error("--url か環境変数 ES_URL を指定してください")
    if not args.user and not args.api_key and os.environ.get("ES_AUTH"):
        args.user, _, args.password = os.environ["ES_AUTH"].partition(":")

    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["Authorization"] = "ApiKey " + args.api_key
    elif args.user:
        headers["Authorization"] = "Basic " + base64.b64encode(f"{args.user}:{args.password}".encode()).decode()
    ctx = ssl._create_unverified_context() if args.insecure else None

    def call(method, path, body=None, raw=False):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(args.url + path, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, context=ctx, timeout=300) as res:
            txt = res.read().decode()
            return txt if raw else json.loads(txt)

    def bench(index, query):
        """1回目 (cold) と 2回目以降の中央値 (warm) を返す"""
        tooks = []
        for _ in range(args.runs):
            r = call("POST", f"/{index}/_search?request_cache=false", query)
            tooks.append(r["took"])
        return tooks[0], statistics.median(tooks[1:]) if len(tooks) > 1 else tooks[0], r

    results = {}
    print("collecting index stats ...")
    cat = call("GET", "/_cat/indices/access-logs-*?format=json&h=index,docs.count,store.size,pri.store.size,segments.count")
    cat = {row["index"]: row for row in cat}
    stats = call("GET", "/access-logs-*/_stats/indexing,store")

    for idx in INDICES:
        if idx not in cat:
            print(f"  skip {idx} (not found)")
            continue
        print(f"running queries on {idx} ...")
        r = {}
        r["docs"] = cat[idx]["docs.count"]
        r["size"] = cat[idx]["store.size"]
        r["segments"] = cat[idx]["segments.count"]
        st = stats["indices"][idx]["primaries"]
        r["index_time_ms"] = st["indexing"]["index_time_in_millis"]
        r["index_total"] = st["indexing"]["index_total"]
        r["agg_cold"], r["agg_warm"], _ = bench(idx, AGG_QUERY)
        r["f1_cold"], r["f1_warm"], resp = bench(idx, FILTER_SORTED)
        r["f1_hits"] = resp["hits"]["total"]["value"]
        r["f2_cold"], r["f2_warm"], resp = bench(idx, FILTER_UNSORTED)
        r["f2_hits"] = resp["hits"]["total"]["value"]
        # シナリオ5: _source の形
        doc = call("GET", f"/{idx}/_search?size=1&q=service.name:order-service")
        r["source"] = json.dumps(doc["hits"]["hits"][0]["_source"], ensure_ascii=False)
        results[idx] = r

    cols = [i for i in INDICES if i in results]
    short = {"access-logs-standard": "standard", "access-logs-logsdb": "logsdb", "access-logs-columnar": "logsdb_columnar"}
    lines = []
    lines.append("| 項目 | " + " | ".join(short[c] for c in cols) + " |")
    lines.append("|---|" + "---|" * len(cols))

    def row(label, key, fmt=lambda v: str(v)):
        lines.append(f"| {label} | " + " | ".join(fmt(results[c][key]) for c in cols) + " |")

    row("ドキュメント数", "docs")
    row("投入済み件数 (index_total)", "index_total")
    row("サーバー側 index 時間 (ms)", "index_time_ms", lambda v: f"{v:,}")
    row("store.size", "size")
    row("セグメント数", "segments")
    row("集計クエリ took 1回目 (ms)", "agg_cold")
    row("集計クエリ took ウォーム中央値 (ms)", "agg_warm")
    row("フィルタ(ソート列) took 1回目 (ms)", "f1_cold")
    row("フィルタ(ソート列) took ウォーム中央値 (ms)", "f1_warm")
    row("フィルタ(ソート列) ヒット数", "f1_hits")
    row("フィルタ(非ソート列) took 1回目 (ms)", "f2_cold")
    row("フィルタ(非ソート列) took ウォーム中央値 (ms)", "f2_warm")
    row("フィルタ(非ソート列) ヒット数", "f2_hits")

    lines.append("")
    lines.append("## _source の形 (1件目)")
    for c in cols:
        lines.append(f"\n### {short[c]}\n```json\n{results[c]['source']}\n```")

    text = "\n".join(lines)
    print("\n" + text)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# Benchmark result ({time.strftime('%Y-%m-%d %H:%M:%S')})\n\n" + text + "\n")
    print(f"\nsaved -> {args.out}")


if __name__ == "__main__":
    main()
