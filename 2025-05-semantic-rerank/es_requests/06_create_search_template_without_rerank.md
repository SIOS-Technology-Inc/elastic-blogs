# RRFを使ったハイブリッド検索を行う検索テンプレートの作成リクエスト

※ハイブリッド検索後のセマンティックリランクは行わない。

```
PUT _scripts/rrf_search_template_without_rerank
{
  "script": {
    "lang": "mustache",
    "source": """{
      "_source": false,
      "fields": [ "chunk_no", "content" ],
      "size": "{{size}}{{^size}}10{{/size}}",
      "retriever": {
        "rrf": {
          "retrievers": [
            {
              "standard": {
                "query": {
                  "match": {
                    "content": "{{query_string}}"
                  }
                }
              }
            },
            {
              "standard": {
                "query": {
                  "semantic": {
                    "field": "content.text_embedding",
                    "query": "{{query_for_vector}}"
                  }
                }
              }
            }
         ],
         "rank_window_size": "{{size}}{{^size}}10{{/size}}",
         "rank_constant": "{{rank_constant}}{{^rank_constant}}20{{/rank_constant}}"
        }
      }
      {{#highlight}}
      ,
      "highlight": {
        "fields": {
          "content": {}
        },
        "pre_tags": ["<strong>"],
        "post_tags": ["</strong>"]
      }
      {{/highlight}}
    }
    """
  }
}
```

キーワード検索　と　ベクトル検索　のハイブリッド検索(RRF)を行います。

検索パラメーターに "highlight": true を指定すると、ハイライトされた結果も返します。

呼び出し例:

```
GET /kakinosuke/_search/template
{
  "id": "rrf_search_template_without_rerank",
  "params": {
    "query_string": "柿之助からおむすびをもらったのは誰?",
    "query_for_vector": "柿之助からおむすびをもらったのは誰?",
    "highlight": true
  }
}
```
