# ハイブリッド検索(ハイライト表示指定可)のテンプレートの作成

```
PUT _scripts/rrf_search_template
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
              "knn": {
                "field": "text_embedding.predicted_value",
                "k": "{{size}}{{^size}}10{{/size}}",
                "num_candidates": "{{num_candidates}}{{^num_candidates}}100{{/num_candidates}}",
                "query_vector_builder": {
                  "text_embedding": {
                    "model_id": ".multilingual-e5-small_linux-x86_64",
                    "model_text": "{{query_for_vector}}"
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
