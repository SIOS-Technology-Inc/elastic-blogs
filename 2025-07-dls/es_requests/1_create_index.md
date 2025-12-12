# create index

```
PUT /dls_sample_202507
{
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "analysis": {
      "filter": {
        "en-stop-words-filter": {
          "type": "stop",
          "stopwords": "_english_"
        }
      },
      "analyzer": {
        "iq_text_base": {
          "filter": [
            "cjk_width",
            "lowercase",
            "asciifolding",
            "en-stop-words-filter"
          ],
          "tokenizer": "standard"
        }
      }
    }
  }
}
```

※あくまでも Document Level Security の動作を確認するためのインデックスなので、
登録内容の形態素解析などは省略しています。

