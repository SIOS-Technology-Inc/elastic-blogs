# リランク用の inference の作成リクエスト

ここでは、 Cohere の rerank-v3.5 を利用します。

```
PUT _inference/rerank/cohere_rerank_v3pt5
{
  "service": "cohere",
  "service_settings": {
    "api_key": "<CohereのAPI-KEY>",
    "model_id": "rerank-v3.5",
    "rate_limit": {
      "requests_per_minute": 10
    }
  },
  "task_settings": {
    "top_n": 10,
    "return_documents": true
  }
}
```

今回は、評価用の Cohere の API Key を利用することを想定しているため、

```
"rate_limit": {
  "requests_per_minute": 10
}
```

を設定しています。

有償契約して、本番で運用する場合には、上限を引き上げてください。
