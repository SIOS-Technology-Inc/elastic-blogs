# インデックスのフィールドの作成

- content フィールドは、日本語形態素解析を行います。

- content.semantic フィールドは、.jina-embedding-v5-text-nano を使って密ベクトルを登録します。

```
PUT /kakinosuke_202609/_mapping
{
  "dynamic": false,
  "properties": {
    "chunk_no": {
      "type": "integer"
    },
    "content": {
      "type": "text",
      "analyzer": "ja_kuromoji_index_analyzer",
      "search_analyzer": "ja_kuromoji_search_analyzer",
      "fields": {
        "semantic": {
          "type": "semantic_text",
          "inference_id": ".jina-embeddings-v5-text-nano"
        }
      }
    }
  }
}
```

