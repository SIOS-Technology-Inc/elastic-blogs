# N-gram検索を行う検索テンプレートの作成

```
PUT _scripts/search_medicine_with_ngram_202505
{
  "script": {
    "lang": "mustache",
    "source": """{
      "_source": false,
      "fields": [ "medicine_code", "medicine_name" ],
      "size": "{{size}}{{^size}}10{{/size}}",
      "query": {
        "bool": {
          "must": [
            {
              "match_phrase": {
                "medicine_name.ngram": "{{search_medicine_name1}}"
              }
            }
            {{#search_medicine_name2}}
            ,
            {
              "match_phrase": {
                "medicine_name.ngram": "{{search_medicine_name2}}"
              }
            }
            {{/search_medicine_name2}}
          ]
        }
      }
    }
    """
  }
}
```

上記の検索テンプレートの利用例:

```
GET /medicine/_search/template
{
  "id": "search_medicine_with_ngram_202505",
  "params": {
    "size": 30,
    "search_medicine_name1": "アス",
    "search_medicine_name2": "100mg"
  }
}
```
