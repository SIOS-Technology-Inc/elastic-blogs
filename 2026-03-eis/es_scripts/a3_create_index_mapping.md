# インデックスのフィールドの作成

```
PUT /waganeko_2026_03/_mapping
{
  "dynamic": false,
  "properties": {
    "chunk_no": {
      "type": "long"
    },
    "content": {
      "type": "text",
      "analyzer": "ja_kuromoji_index_analyzer",
      "search_analyzer": "ja_kuromoji_search_analyzer"
    },
    "content_embedding": {
      "type": "dense_vector",
      "dims": 768,
      "index_options": {
        "type": "bbq_disk",
        "rescore_vector": {
          "oversample": 3.0
        }
      },
      "element_type": "float"
    }
  }
}
```

※dimension は、jina-embedding-v5-text-nano の仕様に合わせて、768 としている。

https://huggingface.co/jinaai/jina-embeddings-v5-text-nano

※本来はデータ量が少ないので、bbq_disk にする必要はないが、検証用にあえて bbq_disk を指定している。
