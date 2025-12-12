# インデックスのフィールドの作成リクエスト

## 作成するフィールド

| フィールド名 | type | 備考 |
|---|---|---|
| content | text | 日本語用のアナライザを設定 |
| content.text_embedding | semantic_text | さらにこのフィールド配下に密ベクトルがチャンク数だけ作成される。 |

## ir_report_2024_chunk_recursive インデックス

```
PUT /ir_report_2024_chunk_recursive/_mappings
{
  "dynamic": false,
  "_source": {
    "excludes": [
      "content.text_embedding"
    ]
  },
  "properties": {
    "content": {
      "type": "text",
      "analyzer": "ja_kuromoji_index_analyzer",
      "search_analyzer": "ja_kuromoji_search_analyzer",
      "fields": {
        "text_embedding": {
          "type": "semantic_text",
          "inference_id": "e5_chunk_recursive"
        }
      }
    }
  }
}
```

