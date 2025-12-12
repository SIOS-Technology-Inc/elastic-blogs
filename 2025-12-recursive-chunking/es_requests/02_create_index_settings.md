# インデックス作成リクエスト

※ユーザー辞書や同義語は設定していません。

## ir_report_2024_chunk_recursive インデックスの作成

```
PUT /ir_report_2024_chunk_recursive
{
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "3600s"
    },
    "analysis": {
      "char_filter": {
        "ja_normalizer": {
          "type": "icu_normalizer",
          "name": "nfkc_cf",
          "mode": "compose"
        }
      },
      "tokenizer": {
        "ja_kuromoji_tokenizer": {
          "mode": "search",
          "type": "kuromoji_tokenizer",
          "discard_compound_token": true
        }
      },
      "analyzer": {
        "ja_kuromoji_index_analyzer": {
          "type": "custom",
          "char_filter": [
            "ja_normalizer",
            "kuromoji_iteration_mark"
          ],
          "tokenizer": "ja_kuromoji_tokenizer",
          "filter": [
            "kuromoji_baseform",
            "kuromoji_part_of_speech",
            "cjk_width",
            "ja_stop",
            "kuromoji_number",
            "kuromoji_stemmer"
          ]
        },
        "ja_kuromoji_search_analyzer": {
          "type": "custom",
          "char_filter": [
            "ja_normalizer",
            "kuromoji_iteration_mark"
          ],
          "tokenizer": "ja_kuromoji_tokenizer",
          "filter": [
            "kuromoji_baseform",
            "kuromoji_part_of_speech",
            "cjk_width",
            "ja_stop",
            "kuromoji_number",
            "kuromoji_stemmer"
          ]
        }
      }
    }
  }
}
```

