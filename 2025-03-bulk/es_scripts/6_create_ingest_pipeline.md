# ドキュメント投入用のパイプラインの作成

```
PUT /_ingest/pipeline/japanese-text-embeddings
{
  "description" : "Text embedding pipeline",
  "processors" : [
    {
      "inference": {
        "model_id": ".multilingual-e5-small_linux-x86_64",
        "target_field": "text_embedding",
        "field_map": {
          "content": "text_field"
        }
      }
    }
  ]
}
```
