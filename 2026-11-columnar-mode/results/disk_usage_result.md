# Disk usage by field (2026-11-09 16:56:31)

## access-logs-standard  (store_size: 135mb)

| field | total | inverted_index | doc_values | stored_fields | points | norms |
|---|---|---|---|---|---|---|
| _source | 77.2mb | 0b | 0b | 77.2mb | 0b | 0b |
| message | 12.4mb | 11.4mb | 0b | 0b | 0b | 976.5kb |
| _id | 12.3mb | 6.3mb | 0b | 6mb | 0b | 0b |
| duration_ms | 5.9mb | 0b | 3.3mb | 0b | 2.6mb | 0b |
| url.path | 5.5mb | 2.9mb | 2.6mb | 0b | 0b | 0b |
| http.response.bytes | 4.9mb | 0b | 2.3mb | 0b | 2.5mb | 0b |
| client.ip | 4.8mb | 0b | 2mb | 0b | 2.7mb | 0b |
| @timestamp | 4.7mb | 0b | 2.8mb | 0b | 1.8mb | 0b |
| _seq_no | 2.9mb | 0b | 1.9mb | 0b | 1mb | 0b |
| http.response.status_code | 1.1mb | 0b | 488.2kb | 0b | 721.5kb | 0b |
| service.name | 1.1mb | 642.8kb | 488.3kb | 0b | 0b | 0b |
| http.request.method | 839.7kb | 351.4kb | 488.3kb | 0b | 0b | 0b |
| service.environment | 447.9kb | 203.7kb | 244.1kb | 0b | 0b | 0b |
| _primary_term | 0b | 0b | 0b | 0b | 0b | 0b |
| _version | 0b | 0b | 0b | 0b | 0b | 0b |

合計: inverted_index 21.9mb / doc_values 16.9mb / stored_fields 83.3mb / points 11.5mb / norms 1.0mb

## access-logs-logsdb  (store_size: 56.8mb)

| field | total | inverted_index | doc_values | stored_fields | points | norms |
|---|---|---|---|---|---|---|
| message | 11.7mb | 11.7mb | 0b | 0b | 0b | 0b |
| message._original | 11.1mb | 0b | 11.1mb | 0b | 0b | 0b |
| _id | 7mb | 4.3mb | 0b | 2.7mb | 0b | 0b |
| duration_ms | 6.4mb | 0b | 3.8mb | 0b | 2.6mb | 0b |
| url.path | 5.3mb | 2.9mb | 2.3mb | 0b | 0b | 0b |
| client.ip | 4.8mb | 0b | 2mb | 0b | 2.7mb | 0b |
| http.response.bytes | 4.4mb | 0b | 1.8mb | 0b | 2.5mb | 0b |
| http.response.status_code | 1.8mb | 0b | 1.1mb | 0b | 720.5kb | 0b |
| @timestamp | 1.5mb | 0b | 1.5mb | 0b | 0b | 0b |
| http.request.method | 844.4kb | 470.5kb | 373.8kb | 0b | 0b | 0b |
| _seq_no | 829.8kb | 0b | 829.8kb | 0b | 0b | 0b |
| service.environment | 618.5kb | 366.7kb | 251.8kb | 0b | 0b | 0b |
| service.name | 58.8kb | 58.7kb | 142b | 0b | 0b | 0b |
| _field_names | 46.5kb | 46.5kb | 0b | 0b | 0b | 0b |
| message._original.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| __root_doc_for_nested | 0b | 0b | 0b | 0b | 0b | 0b |
| _primary_term | 0b | 0b | 0b | 0b | 0b | 0b |
| _recovery_source_size | 0b | 0b | 0b | 0b | 0b | 0b |
| _version | 0b | 0b | 0b | 0b | 0b | 0b |

合計: inverted_index 19.9mb / doc_values 25.5mb / stored_fields 2.7mb / points 8.6mb / norms 0.0mb

## access-logs-columnar  (store_size: 51.1mb)

| field | total | inverted_index | doc_values | stored_fields | points | norms |
|---|---|---|---|---|---|---|
| message | 22.8mb | 11.7mb | 11.1mb | 0b | 0b | 0b |
| _id | 7.9mb | 4.2mb | 3.6mb | 0b | 0b | 0b |
| url.path | 4.5mb | 0b | 4.5mb | 0b | 0b | 0b |
| client.ip | 3.9mb | 0b | 3.9mb | 0b | 0b | 0b |
| duration_ms | 3.8mb | 0b | 3.8mb | 0b | 0b | 0b |
| http.response.bytes | 1.9mb | 0b | 1.9mb | 0b | 0b | 0b |
| @timestamp | 1.5mb | 0b | 1.5mb | 0b | 0b | 0b |
| http.response.status_code | 1.1mb | 0b | 1.1mb | 0b | 0b | 0b |
| service.environment | 904.1kb | 0b | 904.1kb | 0b | 0b | 0b |
| http.request.method | 887.9kb | 0b | 887.9kb | 0b | 0b | 0b |
| _recovery_source_size | 590.8kb | 0b | 590.8kb | 0b | 0b | 0b |
| _seq_no | 519.6kb | 0b | 519.6kb | 0b | 0b | 0b |
| service.name | 502.7kb | 0b | 502.7kb | 0b | 0b | 0b |
| client.ip.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| http.request.method.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| message.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| service.environment.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| service.name.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| url.path.counts | 15.3kb | 0b | 15.3kb | 0b | 0b | 0b |
| __root_doc_for_nested | 0b | 0b | 0b | 0b | 0b | 0b |
| _primary_term | 0b | 0b | 0b | 0b | 0b | 0b |
| _version | 0b | 0b | 0b | 0b | 0b | 0b |

合計: inverted_index 16.0mb / doc_values 35.2mb / stored_fields 0.0mb / points 0.0mb / norms 0.0mb
