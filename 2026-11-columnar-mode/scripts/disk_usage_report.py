#!/usr/bin/env python3
"""
各 index のフィールド別ディスク使用量 (_disk_usage API) を表にする (外部ライブラリ不要)

使い方 (同じフォルダの .env を自動で読む):
  python3 disk_usage_report.py                       # 3 index すべて
  python3 disk_usage_report.py access-logs-columnar  # 1 index だけ
結果は画面に表示し、disk_usage_result.md にも保存する。
"""
import argparse
import json
import os
import sys
import time
import urllib.request


def load_dotenv():
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
            os.environ[key] = value


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("indices", nargs="*", default=["access-logs-standard", "access-logs-logsdb", "access-logs-columnar"])
    ap.add_argument("--out", default="disk_usage_result.md")
    args = ap.parse_args()

    url = os.environ.get("ES_URL")
    headers = {"Content-Type": "application/json"}
    if os.environ.get("ES_API_KEY"):
        headers["Authorization"] = "ApiKey " + os.environ["ES_API_KEY"]
    elif os.environ.get("ES_AUTH"):
        import base64
        headers["Authorization"] = "Basic " + base64.b64encode(os.environ["ES_AUTH"].encode()).decode()
    if not url:
        sys.exit("ES_URL が設定されていません (.env を確認)")
    import ssl
    ctx = ssl._create_unverified_context() if os.environ.get("ES_INSECURE") == "1" else None

    lines = []
    for idx in args.indices:
        req = urllib.request.Request(f"{url}/{idx}/_disk_usage?run_expensive_tasks=true", headers=headers, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=600) as res:
            d = json.loads(res.read())
        body = d[idx]
        fields = body["fields"]
        lines.append(f"\n## {idx}  (store_size: {body['store_size']})\n")
        lines.append("| field | total | inverted_index | doc_values | stored_fields | points | norms |")
        lines.append("|---|---|---|---|---|---|---|")
        for name, f in sorted(fields.items(), key=lambda kv: -kv[1]["total_in_bytes"]):
            lines.append(f"| {name} | {f['total']} | {f['inverted_index']['total']} | {f['doc_values']} | {f['stored_fields']} | {f['points']} | {f['norms']} |")
        # 種類ごとの合計
        tot = {k: 0 for k in ["inverted_index", "doc_values", "stored_fields", "points", "norms"]}
        for f in fields.values():
            tot["inverted_index"] += f["inverted_index"]["total_in_bytes"]
            for k in ["doc_values", "stored_fields", "points", "norms"]:
                tot[k] += f[k + "_in_bytes"]
        mb = lambda b: f"{b / 1024 / 1024:.1f}mb"
        lines.append(f"\n合計: inverted_index {mb(tot['inverted_index'])} / doc_values {mb(tot['doc_values'])} / "
                     f"stored_fields {mb(tot['stored_fields'])} / points {mb(tot['points'])} / norms {mb(tot['norms'])}")

    text = "\n".join(lines)
    print(text)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# Disk usage by field ({time.strftime('%Y-%m-%d %H:%M:%S')})\n" + text + "\n")
    print(f"\nsaved -> {args.out}")


if __name__ == "__main__":
    main()
