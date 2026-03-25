# completion のサンプル

下記を行うクエリーを ES|QL を使って記述する。

- ベクトル検索結果20件とキーワード検索結果20件をRRFを使ってリランクし、上位10件のみとする。
  - ベクトル検索には、.jina-embeddings-v5-text-nano を利用する。

- その結果をセマンティックリランクし、上位1件のみとする。
  - セマンティックリランクには、.jina-reranker-v3 を利用する。

- 上位1件の結果に対し、LLM に質問し、回答してもらう。
  - 質問への回答には、 .openai-gpt-oss-120b-completion を利用する。

```
POST /_query
{
  "query": """
FROM waganeko METADATA _score, _id, _index
| FORK (WHERE MATCH(content, ?query) | SORT _score DESC | LIMIT 20)
       (WHERE KNN(content_embedding, TEXT_EMBEDDING(?query, ".jina-embeddings-v5-text-nano")) | SORT _score DESC | LIMIT 20)
| DROP content_embedding
| FUSE
| SORT _score DESC
| LIMIT 10
| RERANK ?query ON content WITH { "inference_id" : ".jina-reranker-v3" }
| SORT _score DESC
| KEEP content
| LIMIT 1
| COMPLETION CONCAT("Answer in Japanese the following question ", ?query, " based on:\n", content) WITH { "inference_id" : ".openai-gpt-oss-120b-completion" }
""",
  "params": [
    { "query": "吾輩が生まれた場所は?" }
  ]
}
```

回答

```
吾輩は「薄暗く湿った所」、すなわち暗くてじめじめした場所で生まれました。

（「どこで生れたかとんと見当がつかぬ。何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。」という記述に基づく。）
```


## 参考URL

- https://www.elastic.co/search-labs/jp/blog/hybrid-search-multi-stage-retrieval-esql

