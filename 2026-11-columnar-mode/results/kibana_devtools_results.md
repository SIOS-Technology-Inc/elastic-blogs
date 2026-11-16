# Kibana Dev Tools での手動確認（生の結果、2026-11-09）

ブログに貼る用。クエリと結果をそのまま残す。

## 1. 集計クエリ（_search aggs、columnar）

```
POST access-logs-columnar/_search?request_cache=false
{
  "size": 0,
  "aggs": {
    "by_status": {
      "terms": { "field": "http.response.status_code" },
      "aggs": { "avg_duration": { "avg": { "field": "duration_ms" } } }
    }
  }
}
```

結果（took 101ms）。terms の既定 size=10 なので上位 10 件のみ。sum_other_doc_count 29,876。

| status_code | doc_count | avg_duration (ms) |
|---|---|---|
| 200 | 720,292 | 45.59 |
| 304 | 59,916 | 45.57 |
| 404 | 50,029 | 45.94 |
| 201 | 40,051 | 45.54 |
| 400 | 25,058 | 45.52 |
| 204 | 19,798 | 45.89 |
| 401 | 14,995 | 45.60 |
| 500 | 14,993 | 526.60 |
| 302 | 14,821 | 45.75 |
| 301 | 10,171 | 46.14 |

## 2. ES|QL 版（columnar）

```
POST _query
{
  "query": "FROM access-logs-columnar | STATS avg_duration = AVG(duration_ms) BY http.response.status_code | SORT http.response.status_code"
}
```

結果（took 365ms、documents_found 1,000,000、values_loaded 2,000,000、cpu_nanos 954,397,977）。全 14 種類が出る。

| status_code | avg_duration (ms) |
|---|---|
| 200 | 45.59 |
| 201 | 45.54 |
| 204 | 45.89 |
| 301 | 46.14 |
| 302 | 45.75 |
| 304 | 45.57 |
| 400 | 45.52 |
| 401 | 45.60 |
| 403 | 46.20 |
| 404 | 45.94 |
| 429 | 2.74 |
| 500 | 526.60 |
| 502 | 524.91 |
| 503 | 520.04 |

## 3. url.path の完全一致（standard と columnar の比較）

```
GET access-logs-standard/_search?size=1&q=url.path:"/api/v1/products/item-9823"
GET access-logs-columnar/_search?size=1&q=url.path:"/api/v1/products/item-9823"
```

| | standard | columnar |
|---|---|---|
| took | 1 ms | 53 ms |
| hits.total | 3 | 3 |
| max_score | 12.562749 | 1 |
| _source の形 | ネストした JSON | 平らなドット区切り |

standard の _source：
```json
{"@timestamp": "2026-11-06T16:28:16.111Z", "http": {"request": {"method": "POST"}, "response": {"status_code": 200, "bytes": 1409}}, "client": {"ip": "42.109.12.103"}, "url": {"path": "/api/v1/products/item-9823"}, "duration_ms": 45, "service": {"name": "order-service", "environment": "development"}, "message": "POST /api/v1/products/item-9823 HTTP/1.1 200 1409 45.0ms"}
```

columnar の _source：
```json
{"@timestamp": "2026-11-06T03:45:53.991Z", "client.ip": "192.168.34.174", "duration_ms": 27.3, "http.request.method": "GET", "http.response.bytes": 624, "http.response.status_code": 200, "message": "GET /api/v1/products/item-9823 HTTP/1.1 200 624 27.3ms", "service.environment": "production", "service.name": "inventory-service", "url.path": "/api/v1/products/item-9823"}
```

## 4. message への全文検索（columnar）

```
GET access-logs-columnar/_search?size=1
{ "query": { "match": { "message": "item-9823" } } }
```

結果：took 19ms、hits.total 10,000 以上（gte）、max_score 19.44191。text 型の message は columnar でも転置インデックスが残るので、全文検索とスコア付けが通常どおり動く。
注意：standard analyzer が "item-9823" を "item" と "9823" に分けるため、OR 検索となり多数ヒットする。完全一致なら match_phrase を使う。
