# Ingest 用 pipeline

content フィールドに文字列を格納したら、content を密ベクトルに変換した値を
content_embedding に自動的に格納するよう、_ingest/pipeline を作成しておく。

```
PUT _ingest/pipeline/eis_jina_embeddings_pipeline
{
  "processors": [
    {
      "inference": {
        "model_id": ".jina-embeddings-v5-text-nano",
        "input_output": {
          "input_field": "content",
          "output_field": "content_embedding"
        }
      }
    }
  ]
}
```

※ ".jina-embeddings-v5-text-nano" を Self-Managed の Elasticsearch にインストールすることなく、利用できる点に注目。

## 参考URL

- https://www.elastic.co/docs/solutions/search/semantic-search/semantic-search-inference

使える model_id は、ここに出てくる。

Elasticsearch / Relevance / Inference endpoints

http://localhost:5601/app/elasticsearch/relevance/inference_endpoints

