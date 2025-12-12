# インデックスのフィールドの作成リクエスト

```
PUT /sios_securities_report/_mappings
{
  "dynamic": false,
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "fiscal_year": {
          "type": "keyword"
        }
      }
    },
    "chunk_no": {
      "type": "integer"
    },
    "content": {
      "type": "text",
      "analyzer": "ja_kuromoji_index_analyzer",
      "search_analyzer": "ja_kuromoji_index_analyzer"
    }
  }
}
```

