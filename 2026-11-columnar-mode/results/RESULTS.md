# 検証結果（Elastic Cloud Hosted、2026-11-09）

環境：Elastic Cloud Hosted / columnar-test / AWS ap-northeast-1 / Elasticsearch 9.5.6 / license enterprise
構成：1 シャード・レプリカ 0 / 3 index とも同じマッピング / logsdb と columnar は sort = service.name asc, @timestamp desc
データ：Web アクセスログ 100 万件（24 時間分、NDJSON 334MB）
クライアント：Mac から HTTPS 経由、Bulk 5,000 件ずつ、単一スレッド

## シナリオ 1：取り込み性能

| index | モード | クライアント所要時間 | docs/sec | サーバー側 index 時間 (index_time_in_millis) | errors |
|---|---|---|---|---|---|
| access-logs-standard | standard | 120.0 s | 8,335 | 35,135 ms | 0 |
| access-logs-logsdb | logsdb | 123.5 s | 8,094 | 38,222 ms | 0 |
| access-logs-columnar | logsdb_columnar | 121.0 s | 8,263 | 35,790 ms | 0 |

所見：
- クライアント側の時間は 3 つとも約 120 秒で差なし。ネットワークとクライアントが上限。
- サーバー側の index 時間も 35〜38 秒でほぼ同じ。columnar は logsdb より 6% 短く、standard と同等。
- 転置インデックスを作らない分の節約はあるが、doc values の書き込みや _source 相当の処理があるため、大きな差にはならなかった。

## シナリオ 2：ディスク使用量（forcemerge で 1 セグメントにした後）

| index | モード | store.size | standard 比 | logsdb 比 |
|---|---|---|---|---|
| access-logs-standard | standard | 135 mb | 100% | |
| access-logs-logsdb | logsdb | 56.8 mb | 42%（58% 減） | 100% |
| access-logs-columnar | logsdb_columnar | 51.1 mb | 38%（62% 減） | 90%（10% 減） |

注意：forcemerge 直後の 1 回目の計測では columnar 66.9mb / logsdb 90mb だった。2 回目の forcemerge 後に上記の値に落ち着いた。
古いセグメントのファイルが残っていたためと考えられる。サイズ比較は forcemerge を 2 回実行するか、数分おいて再計測する。

### 保存形式ごとの合計（_disk_usage）

| 保存形式 | standard | logsdb | logsdb_columnar |
|---|---|---|---|
| stored_fields（_source など） | 83.3 mb | 2.7 mb | 0 mb |
| inverted_index（転置インデックス） | 21.9 mb | 19.9 mb | 16.0 mb |
| points（数値・IP・日付の BKD 木） | 11.5 mb | 8.6 mb | 0 mb |
| doc_values（列データ） | 16.9 mb | 25.5 mb | 35.2 mb |
| norms | 1.0 mb | 0 mb | 0 mb |

所見：
- standard の 135mb のうち 77mb（57%）は _source（元の JSON）の保存。logsdb と columnar はこれを持たない（synthetic _source）。
- columnar は points（数値・IP・日付の検索用インデックス）がゼロ。keyword の転置インデックスもゼロ。残る転置インデックスは message（text、11.7mb）と _id（4.2mb）だけ。
- その代わり doc_values が増える（35.2mb）。「各フィールドを doc values として 1 回だけ保存する」という設計どおり。
- message は columnar で転置インデックス 11.7mb と doc values 11.1mb の両方を持つ（_source 復元のため）。logsdb では message._original という別フィールドに同じ役割の 11.1mb がある。
- columnar では _id も doc values に保存される（stored_fields ではなく）。

### フィールド別（主要なもの）

| field | standard inverted / dv / points | logsdb inverted / dv / points | columnar inverted / dv / points |
|---|---|---|---|
| url.path | 2.9 / 2.6 / 0 | 2.9 / 2.3 / 0 | 0 / 4.5 / 0 |
| client.ip | 0 / 2.0 / 2.7 | 0 / 2.0 / 2.7 | 0 / 3.9 / 0 |
| duration_ms | 0 / 3.3 / 2.6 | 0 / 3.8 / 2.6 | 0 / 3.8 / 0 |
| http.response.bytes | 0 / 2.3 / 2.5 | 0 / 1.8 / 2.5 | 0 / 1.9 / 0 |
| @timestamp | 0 / 2.8 / 1.8 | 0 / 1.5 / 0 | 0 / 1.5 / 0 |
| service.name | 0.6 / 0.5 / 0 | 0.06 / 0.0001 / 0 | 0 / 0.5 / 0 |
| message | 11.4 / 0 / 0 | 11.7 / 0 (+_original 11.1) / 0 | 11.7 / 11.1 / 0 |

（単位 mb。dv = doc_values）

## シナリオ 3：集計クエリ（ステータスコード別の平均レスポンス時間、request_cache=false、5 回）

| | standard | logsdb | logsdb_columnar |
|---|---|---|---|
| took 1 回目（コールド） | 168 ms | 136 ms | 102 ms |
| took ウォーム中央値 | 112.5 ms | 103.5 ms | 101.0 ms |

所見：集計はもともと doc values を読む処理なので、ウォームでは 3 つとも約 100ms で同等。コールドでは columnar が最も速い（standard の 6 割）。

## シナリオ 4：フィルタクエリ（転置インデックスがないフィールドでの絞り込み）

| クエリ | standard | logsdb | logsdb_columnar | ヒット数 |
|---|---|---|---|---|
| ソート列で絞る（service.name + status>=500 + 1 時間の範囲）ウォーム中央値 | 3.0 ms | 2.0 ms | 15.0 ms | 251 |
| 同上 1 回目 | 14 ms | 12 ms | 42 ms | 251 |
| 非ソート列で絞る（url.path = 1 つのパス）ウォーム中央値 | 0.0 ms | 0.0 ms | 51.0 ms | 3 |
| 同上 1 回目 | 0 ms | 0 ms | 52 ms | 3 |

所見：
- ここが Columnar モードのトレードオフ。standard と logsdb は転置インデックスと BKD 木で一瞬で絞れる（0〜3ms）。
- columnar は転置インデックスがないため doc values を読んで絞る。ソート列（service.name、@timestamp）では doc values skipper が効いて 15ms。
- ソートに入っていない url.path の完全一致は、100 万件の doc values を走査するため 51ms。それでも 100 万件で 51ms なので、ログ分析の用途では実用範囲。
- 使い分けの目安：「特定の 1 件を ID やパスで探す」用途が多いなら standard / logsdb。「集計と時系列の絞り込み」が中心なら columnar。

## シナリオ 5：_source の形

| モード | 返ってくる _source |
|---|---|
| standard | 投入した JSON そのまま（キーの順序も同じ） |
| logsdb | 内容は同じだが、キーがアルファベット順に並び替わる（synthetic _source）。ネストした形は保たれる |
| logsdb_columnar | 平らなドット区切り。`"service.name": "order-service"` のように返る。ネストした形は失われる |

columnar の実例：
```json
{"@timestamp": "2026-11-06T23:58:40.150Z", "client.ip": "192.168.77.167", "duration_ms": 51.1, "http.request.method": "GET", "http.response.bytes": 7475, "http.response.status_code": 200, "message": "GET /api/v1/users/11308/orders HTTP/1.1 200 7475 51.1ms", "service.environment": "production", "service.name": "order-service", "url.path": "/api/v1/users/11308/orders"}
```

所見：値は 1 つも失われていないが、形が変わる。ネストした JSON をそのまま使うアプリケーションがある場合は、受け取り側の対応が必要。

## Kibana Dev Tools での手動確認（詳細は kibana_devtools_results.md）

| 確認項目 | 結果 | 読み方 |
|---|---|---|
| _search 集計（columnar） | took 101ms | run_benchmark.py の値と一致。5xx の平均 約 526ms、それ以外 約 45ms とデータの相関が見える |
| ES\|QL 集計（columnar） | took 365ms、values_loaded 2,000,000 | 読み込んだ値が「2 列 × 100 万件」ちょうど。必要な列だけ読む列指向の動きが数字で確認できる。took は _search より大きいが、1 回のみの計測 |
| url.path 完全一致 | standard 1ms（_score 12.56）/ columnar 53ms（_score 1） | columnar は doc values で絞るため遅く、スコアも付かない（定数 1）。転置インデックスの有無がそのまま出る |
| message の match（columnar） | took 19ms、スコア 19.44 | text 型は columnar でも転置インデックスが残るので、全文検索は通常どおり |
| _source の形 | standard はネスト、columnar は平ら | 同じ検索条件で 1 件ずつ取り出して並べた実例を保存済み |

新しい発見：転置インデックスがない keyword フィールドへの検索は、速度だけでなく _score も変わる（常に 1）。関連度順に並べたい用途には向かない。

## まとめ（ブログの結論に使う）

| 観点 | 結果 |
|---|---|
| ディスク | standard 比 62% 減、logsdb 比 10% 減 |
| 取り込み | 差なし（サーバー側 35〜38 秒で同等） |
| 集計 | 同等（ウォーム約 100ms）、コールドは columnar が最速 |
| 絞り込み | columnar が遅い（0〜3ms → 15〜51ms）。ただし 100 万件で 50ms 台 |
| _source | 平らな形になる |
