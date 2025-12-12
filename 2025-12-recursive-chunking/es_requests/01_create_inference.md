# Text Embedding 用の inference endpoint の作成リクエスト

## 前提条件

事前に、.multilingual-e5-small_linux-x86_64 のモデルをデプロイしておく必要があります。

## strategy: recursive

```
PUT _inference/text_embedding/e5_chunk_recursive
{
  "service": "elasticsearch",
      "service_settings": {
        "num_allocations": 1,
        "num_threads": 1,
        "model_id": ".multilingual-e5-small_linux-x86_64"
      },
      "chunking_settings": {
        "strategy": "recursive",
        "max_chunk_size": 300,
        "separators": [
          "\n# ",
          "\n## ",
          "\n### ",
          "\n#### ",
          "\n##### ",
          "\n###### "
        ]
      }
}
```

