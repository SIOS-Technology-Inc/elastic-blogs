# Benchmark result (2026-11-09 16:58:27)

| 項目 | standard | logsdb | logsdb_columnar |
|---|---|---|---|
| ドキュメント数 | 1000000 | 1000000 | 1000000 |
| 投入済み件数 (index_total) | 1000000 | 1000000 | 1000000 |
| サーバー側 index 時間 (ms) | 35,135 | 38,222 | 35,790 |
| store.size | 135mb | 56.8mb | 51.1mb |
| セグメント数 | 1 | 1 | 1 |
| 集計クエリ took 1回目 (ms) | 168 | 136 | 102 |
| 集計クエリ took ウォーム中央値 (ms) | 112.5 | 103.5 | 101.0 |
| フィルタ(ソート列) took 1回目 (ms) | 14 | 12 | 42 |
| フィルタ(ソート列) took ウォーム中央値 (ms) | 3.0 | 2.0 | 15.0 |
| フィルタ(ソート列) ヒット数 | 251 | 251 | 251 |
| フィルタ(非ソート列) took 1回目 (ms) | 0 | 0 | 52 |
| フィルタ(非ソート列) took ウォーム中央値 (ms) | 0.0 | 0.0 | 51.0 |
| フィルタ(非ソート列) ヒット数 | 3 | 3 | 3 |

## _source の形 (1件目)

### standard
```json
{"@timestamp": "2026-11-06T00:00:00.427Z", "http": {"request": {"method": "PUT"}, "response": {"status_code": 200, "bytes": 4439}}, "client": {"ip": "189.5.5.78"}, "url": {"path": "/api/v1/products"}, "duration_ms": 63.5, "service": {"name": "order-service", "environment": "production"}, "message": "PUT /api/v1/products HTTP/1.1 200 4439 63.5ms"}
```

### logsdb
```json
{"@timestamp": "2026-11-06T23:58:40.150Z", "client": {"ip": "192.168.77.167"}, "duration_ms": 51.1, "http": {"request": {"method": "GET"}, "response": {"bytes": 7475, "status_code": 200}}, "message": "GET /api/v1/users/11308/orders HTTP/1.1 200 7475 51.1ms", "service": {"environment": "production", "name": "order-service"}, "url": {"path": "/api/v1/users/11308/orders"}}
```

### logsdb_columnar
```json
{"@timestamp": "2026-11-06T23:58:40.150Z", "client.ip": "192.168.77.167", "duration_ms": 51.1, "http.request.method": "GET", "http.response.bytes": 7475, "http.response.status_code": 200, "message": "GET /api/v1/users/11308/orders HTTP/1.1 200 7475 51.1ms", "service.environment": "production", "service.name": "order-service", "url.path": "/api/v1/users/11308/orders"}
```
