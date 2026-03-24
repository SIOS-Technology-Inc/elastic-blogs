# ES|QL での RRF and Semantic Rerank


下記を行うクエリーを ES|QL を使って記述する。

- ベクトル検索結果20件とキーワード検索結果20件をRRFを使ってリランクし、上位10件のみとする。
  - ベクトル検索には、.jina-embeddings-v5-text-nano を利用する。

- その結果をセマンティックリランクする。
  - セマンティックリランクには、.jina-reranker-v3 を利用する。

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
| KEEP chunk_no, content, _score
| SORT _score DESC
""",
  "params": [
    { "query": "吾輩が生まれた場所は?" }
  ]
}
```

検索結果

```
...
  "values": [
    [
      2,
      "どこで生れたかとんと見当がつかぬ。何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。吾輩はここで始めて人間というものを見た。しかもあとで聞くとそれは書生という人間中で一番獰悪な種族であったそうだ。この書生というのは時々我々を捕えて煮て食うという話である。しかしその当時は何という考もなかったから別段恐しいとも思わなかった。",
      0.33165714144706726
    ],
    [
      1217,
      "しばらくは爺さんの方へ気を取られて他の化物の事は全く忘れていたのみならず、苦しそうにすくんでいた主人さえ記憶の中から消え去った時突然流しと板の間の中間で大きな声を出すものがある。見ると紛れもなき苦沙弥先生である。主人の声の図抜けて大いなるのと、その濁って聴き苦しいのは今日に始まった事ではないが場所が場所だけに吾輩は少からず驚ろいた。",
      0.08227790892124176
    ],
    ...
]
...
```

## 参考URL

https://www.elastic.co/search-labs/jp/blog/hybrid-search-multi-stage-retrieval-esql
