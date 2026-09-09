# Reindex

## 準備

- 事前に kakinosuke_chunked.json を kakinosuke_tmp インデックスへ upload しておくこと。

- 事前に Self-Managed の Elasticsearch から EIS 経由で .jina-embeddings-v5-text-nano モデルを利用できるよう設定しておくこと。

## reindex

```
POST _reindex?wait_for_completion=true&refresh
{
  "source": {
    "index": "kakinosuke_tmp"
  },
  "dest": {
    "index": "kakinosuke_202609"
  }
}
```

※_reindex を行うと、日本語形態素解析が行われます。また、密ベクトルの生成・登録も行われます。

## 確認

登録したドキュメント数

```
GET /kakinosuke_202609/_count
```

Response : 38


密ベクトルが格納されているか、確認します。

```
GET /kakinosuke_202609/_search?size=3
{
    "query": {
        "match": {
          "content": "柿之助"
        }
    },
    "fields": [
      "_inference_fields"
    ]
}
```


## disk 使用量の確認

```
POST /kakinosuke_202609/_disk_usage?run_expensive_tasks=true
```

```
{
  "_shards": {
    "total": 1,
    "successful": 1,
    "failed": 0
  },
  "kakinosuke_202609": {
    "store_size": "92.9kb",
    "store_size_in_bytes": 95144,
    "all_fields": {
      "total": "81.3kb",
      "total_in_bytes": 83350,
      "inverted_index": {
        "total": "9.3kb",
        "total_in_bytes": 9541
      },
      "stored_fields": "10.4kb",
      "stored_fields_in_bytes": 10665,
      "doc_values": "280b",
      "doc_values_in_bytes": 280,
      "points": "192b",
      "points_in_bytes": 192,
      "norms": "124b",
      "norms_in_bytes": 124,
      "term_vectors": "0b",
      "term_vectors_in_bytes": 0,
      "knn_vectors": "61kb",
      "knn_vectors_in_bytes": 62548,
      "bloom_filter": "0b",
      "bloom_filter_in_bytes": 0
    },
    "fields": {
      "_field_names": {
        "total": "104b",
        "total_in_bytes": 104,
        "inverted_index": {
          "total": "104b",
          "total_in_bytes": 104
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "_id": {
        "total": "1.3kb",
        "total_in_bytes": 1349,
        "inverted_index": {
          "total": "820b",
          "total_in_bytes": 820
        },
        "stored_fields": "529b",
        "stored_fields_in_bytes": 529,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "_nested_path": {
        "total": "98b",
        "total_in_bytes": 98,
        "inverted_index": {
          "total": "98b",
          "total_in_bytes": 98
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "_primary_term": {
        "total": "80b",
        "total_in_bytes": 80,
        "inverted_index": {
          "total": "0b",
          "total_in_bytes": 0
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "80b",
        "doc_values_in_bytes": 80,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "_seq_no": {
        "total": "165b",
        "total_in_bytes": 165,
        "inverted_index": {
          "total": "0b",
          "total_in_bytes": 0
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "76b",
        "doc_values_in_bytes": 76,
        "points": "89b",
        "points_in_bytes": 89,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "_source": {
        "total": "9.8kb",
        "total_in_bytes": 10136,
        "inverted_index": {
          "total": "0b",
          "total_in_bytes": 0
        },
        "stored_fields": "9.8kb",
        "stored_fields_in_bytes": 10136,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "_version": {
        "total": "0b",
        "total_in_bytes": 0,
        "inverted_index": {
          "total": "0b",
          "total_in_bytes": 0
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "chunk_no": {
        "total": "227b",
        "total_in_bytes": 227,
        "inverted_index": {
          "total": "0b",
          "total_in_bytes": 0
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "124b",
        "doc_values_in_bytes": 124,
        "points": "103b",
        "points_in_bytes": 103,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "content": {
        "total": "8.2kb",
        "total_in_bytes": 8429,
        "inverted_index": {
          "total": "8.1kb",
          "total_in_bytes": 8305
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "124b",
        "norms_in_bytes": 124,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "content.semantic.inference.chunks.embeddings": {
        "total": "61kb",
        "total_in_bytes": 62548,
        "inverted_index": {
          "total": "0b",
          "total_in_bytes": 0
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "61kb",
        "knn_vectors_in_bytes": 62548,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      },
      "content.semantic.inference.chunks.offset": {
        "total": "214b",
        "total_in_bytes": 214,
        "inverted_index": {
          "total": "214b",
          "total_in_bytes": 214
        },
        "stored_fields": "0b",
        "stored_fields_in_bytes": 0,
        "doc_values": "0b",
        "doc_values_in_bytes": 0,
        "points": "0b",
        "points_in_bytes": 0,
        "norms": "0b",
        "norms_in_bytes": 0,
        "term_vectors": "0b",
        "term_vectors_in_bytes": 0,
        "knn_vectors": "0b",
        "knn_vectors_in_bytes": 0,
        "bloom_filter": "0b",
        "bloom_filter_in_bytes": 0
      }
    }
  }
}
```


knn_vectors_in_bytes : 62548

document count = 38 なので、1 document あたり = 62548 / 38 = 1646 bytes

1646 / 768 = 2.14... つまり 1要素あたり2バイト強なので、bfloat16 になっていることがわかります。



