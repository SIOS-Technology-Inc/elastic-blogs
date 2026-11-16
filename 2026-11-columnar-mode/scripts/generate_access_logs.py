#!/usr/bin/env python3
"""
Webアクセスログ生成スクリプト（Elastic Columnar モード検証用）

使い方:
  python3 generate_access_logs.py                      # 1,000,000件を access_logs.ndjson に出力
  python3 generate_access_logs.py --count 10000        # 件数を変える
  python3 generate_access_logs.py --bulk               # Bulk API 用（action行つき）で出力
  python3 generate_access_logs.py --seed 1             # 乱数シードを固定（再現性）

出力は NDJSON（1行1ドキュメント）。外部ライブラリ不要。
"""
import argparse
import itertools
import json
import random
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------
# 1. 値の候補（低カーディナリティ = 種類が少ない。Columnar の圧縮が効きやすい）
# ---------------------------------------------------------------
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]
METHOD_WEIGHTS = [70, 18, 5, 3, 2, 2]

SERVICES = [
    "order-service", "product-service", "user-service", "cart-service",
    "payment-service", "search-service", "inventory-service", "auth-service",
    "notification-service", "api-gateway",
]
SERVICE_WEIGHTS = [20, 25, 12, 10, 8, 10, 5, 5, 2, 3]

ENVIRONMENTS = ["production", "staging", "development"]
ENV_WEIGHTS = [85, 10, 5]

# ステータスコード（成功が多く、エラーは少なめ）
STATUS_CODES = [200, 201, 204, 301, 302, 304, 400, 401, 403, 404, 429, 500, 502, 503]
STATUS_WEIGHTS = [720, 40, 20, 10, 15, 60, 25, 15, 10, 50, 5, 15, 8, 7]

# ---------------------------------------------------------------
# 2. URLパス（中〜高カーディナリティ。固定パス + IDつきパスを混ぜる）
# ---------------------------------------------------------------
STATIC_PATHS = [
    "/", "/health", "/metrics", "/login", "/logout", "/api/v1/products",
    "/api/v1/cart", "/api/v1/orders", "/api/v1/users/me", "/api/v1/search",
    "/static/app.js", "/static/style.css", "/favicon.ico", "/robots.txt",
]
DYNAMIC_PATH_TEMPLATES = [
    "/api/v1/products/item-{id}",
    "/api/v1/orders/{id}",
    "/api/v1/users/{id}",
    "/api/v1/users/{id}/orders",
    "/api/v1/cart/{id}/items",
    "/api/v2/products/{id}/reviews",
    "/images/products/{id}.jpg",
]


def make_path(rnd):
    # 40% は固定パス、60% はIDつきパス
    if rnd.random() < 0.4:
        return rnd.choice(STATIC_PATHS)
    tpl = rnd.choice(DYNAMIC_PATH_TEMPLATES)
    return tpl.format(id=rnd.randint(1, 20000))


# ---------------------------------------------------------------
# 3. クライアントIP（プールを作って再利用 → 同じIPが何度も出る現実的な形）
# ---------------------------------------------------------------
def build_ip_pool(rnd, size):
    pool = []
    for _ in range(size):
        kind = rnd.random()
        if kind < 0.5:    # 社内っぽいIP
            ip = f"192.168.{rnd.randint(0, 255)}.{rnd.randint(1, 254)}"
        elif kind < 0.7:
            ip = f"10.{rnd.randint(0, 255)}.{rnd.randint(0, 255)}.{rnd.randint(1, 254)}"
        else:             # グローバルっぽいIP
            ip = f"{rnd.randint(11, 223)}.{rnd.randint(0, 255)}.{rnd.randint(0, 255)}.{rnd.randint(1, 254)}"
        pool.append(ip)
    return pool


# ---------------------------------------------------------------
# 4. 1件のログを作る
# ---------------------------------------------------------------
def make_log(rnd, ts, ip_pool, ip_weights):
    method = rnd.choices(METHODS, METHOD_WEIGHTS)[0]
    status = rnd.choices(STATUS_CODES, STATUS_WEIGHTS)[0]
    path = make_path(rnd)
    ip = rnd.choices(ip_pool, cum_weights=ip_weights)[0]
    service = rnd.choices(SERVICES, SERVICE_WEIGHTS)[0]
    env = rnd.choices(ENVIRONMENTS, ENV_WEIGHTS)[0]

    # レスポンスサイズ: 304/204 は 0、それ以外は対数正規っぽい分布
    if status in (204, 304):
        size = 0
    elif status >= 500:
        size = rnd.randint(100, 600)
    else:
        size = int(rnd.lognormvariate(8.0, 1.0))  # 中央値 約3000 bytes
        size = min(size, 5_000_000)

    # 処理時間: 遅いリクエストは少数。5xx は遅くなりがち
    duration = rnd.lognormvariate(3.5, 0.8)  # 中央値 約33ms
    if status >= 500:
        duration *= rnd.uniform(3, 20)
    elif status == 429:
        duration = rnd.uniform(0.5, 5.0)
    duration = round(min(duration, 60_000.0), 1)

    message = f"{method} {path} HTTP/1.1 {status} {size} {duration}ms"

    return {
        "@timestamp": ts,
        "http": {
            "request": {"method": method},
            "response": {"status_code": status, "bytes": size},
        },
        "client": {"ip": ip},
        "url": {"path": path},
        "duration_ms": duration,
        "service": {"name": service, "environment": env},
        "message": message,
    }


# ---------------------------------------------------------------
# 5. メイン
# ---------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Webアクセスログ(NDJSON)を生成する")
    ap.add_argument("--count", type=int, default=1_000_000, help="生成件数 (default: 1,000,000)")
    ap.add_argument("--out", default="access_logs.ndjson", help="出力ファイル名")
    ap.add_argument("--seed", type=int, default=42, help="乱数シード")
    ap.add_argument("--start", default="2026-11-06T00:00:00Z", help="開始時刻 (UTC, ISO8601)")
    ap.add_argument("--hours", type=float, default=24.0, help="何時間分のログにするか")
    ap.add_argument("--ip-pool", type=int, default=50_000, help="クライアントIPの種類数")
    ap.add_argument("--bulk", action="store_true", help="Bulk API 形式 (action行つき) で出力")
    ap.add_argument("--index", default="access-logs", help="--bulk 時の index 名")
    args = ap.parse_args()

    rnd = random.Random(args.seed)
    start = datetime.strptime(args.start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    total_ms = int(args.hours * 3600 * 1000)

    ip_pool = build_ip_pool(rnd, args.ip_pool)
    # 一部のIPがよく出るように重みをつける（べき乗分布っぽく）
    ip_weights = [1.0 / (i + 1) ** 0.6 for i in range(len(ip_pool))]
    rnd.shuffle(ip_weights)
    # 累積重みを事前計算（毎回計算すると非常に遅くなるため）
    ip_weights = list(itertools.accumulate(ip_weights))

    # タイムスタンプは昇順。平均間隔のまわりでランダムにずらす
    avg_gap = total_ms / args.count
    cur_ms = 0.0

    action_line = json.dumps({"index": {"_index": args.index}}, separators=(",", ":")) + "\n"
    dumps = json.dumps
    report_every = max(args.count // 20, 1)

    with open(args.out, "w", encoding="utf-8") as f:
        for i in range(args.count):
            cur_ms += rnd.expovariate(1.0 / avg_gap)
            ts_dt = start + timedelta(milliseconds=int(cur_ms))
            ts = ts_dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts_dt.microsecond // 1000:03d}Z"
            doc = make_log(rnd, ts, ip_pool, ip_weights)
            if args.bulk:
                f.write(action_line)
            f.write(dumps(doc, separators=(",", ":"), ensure_ascii=False))
            f.write("\n")
            if (i + 1) % report_every == 0:
                print(f"  {i + 1:,} / {args.count:,}", flush=True)

    print(f"done: {args.count:,} docs -> {args.out}")


if __name__ == "__main__":
    main()
