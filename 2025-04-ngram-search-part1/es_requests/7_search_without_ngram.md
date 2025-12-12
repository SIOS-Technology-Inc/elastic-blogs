# N-gramを利用しない検索リクエスト

```
GET /ngram_sample_202504/_search
{
  "query": {
    "match": {
      "content": "タイパ"
    }
  }
}
```
