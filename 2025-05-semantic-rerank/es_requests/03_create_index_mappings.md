# インデックスのフィールドの作成リクエスト


```
PUT /kakinosuke_202505/_mappings
{
  "dynamic": false,
  "_source": {
    "excludes": [
      "content.text_embedding"
    ]
  },
  "properties": {
    "chunk_no": {
      "type": "integer"
    },
    "content": {
      "type": "text",
      "analyzer": "ja_kuromoji_index_analyzer",
      "search_analyzer": "ja_kuromoji_search_analyzer",
      "fields": {
        "text_embedding": {
          "type": "semantic_text",
          "inference_id": ".multilingual-e5-small-elasticsearch"
        }
      }
    }
  }
}
```

ベクトルは、content.text_embedding フィールド (type : semantic_text) に格納します。


## ※ベクトル生成用のパイプライン

今回は、密ベクトルの生成に .multilingual-e5-small_linux-x86_64 を利用しています。

このモデルを利用する場合、以前のバージョンではドキュメント登録後のベクトル生成用の
inference を事前に作成しておく必要がありました。

Elasticsearch v8.18 では、あらかじめ
__.multilingual-e5-small-elasticsearch__
という名前で inference が用意されています。
今回は、これを利用しています。

