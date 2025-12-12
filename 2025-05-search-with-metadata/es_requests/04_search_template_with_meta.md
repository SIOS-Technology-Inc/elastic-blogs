# メタ情報による絞り込みを可能とした検索テンプレートの作成リクエスト

```
PUT _scripts/search_with_meta_template_202505
{
  "script": {
    "lang": "mustache",
    "source": """{
      "_source": false,
      "fields": [ "meta.fiscal_year", "chunk_no", "content" ],
      "size": "{{size}}{{^size}}10{{/size}}",
      "query": {
        "bool": {
          "must": [
            {
              "match": {
                "content": "{{query}}"
               }
            }
          ]
          {{#fiscal_year}}
          ,
          "filter": [
            {
              "term": {
                "meta.fiscal_year": "{{fiscal_year}}"
              }
            }
          ]
          {{/fiscal_year}}
        }
      }
    }
    """
  }
}
```

