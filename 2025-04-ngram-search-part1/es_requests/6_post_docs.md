# 検証用のドキュメントの登録リクエスト

```
POST /ngram_sample_202504/_doc
{ "chunk_no": 1, "content": "最近は、タイパを重視して行動する人が多くなった。" }

POST /ngram_sample_202504/_doc
{ "chunk_no": 2, "content": "タイムズスクエア近くでパーティーがあった。" }

POST /ngram_sample_202504/_doc
{ "chunk_no": 3, "content": "タイムズスクエア近くで何かのパフォーマンスが行われた。" }

POST /ngram_sample_202504/_doc
{ "chunk_no": 4, "content": "タイには、なんとか「パ」というお店があるとか、ないとか。" }

POST /ngram_sample_202504/_doc
{ "chunk_no": 5, "content": "タイには、「パ」で始まる名前が多いとか、少ないとか。" }

POST /ngram_sample_202504/_doc
{ "chunk_no": 6, "content": "タイのパなんとかという地域に、珍しい食べ物があったとか、なかったとか。。" }

POST /ngram_sample_202504/_refresh
```

