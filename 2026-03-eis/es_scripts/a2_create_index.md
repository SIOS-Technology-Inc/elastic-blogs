# インデックスの作成

「吾輩は猫である」のデータを格納するためのインデックスの作成。

日本語の形態素解析を行うため、icu や kuromoji の設定をしておく。

```
PUT /waganeko_2026_03/
{
  "settings": {
    "index": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
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
          "discard_compound_token": true,
          "user_dictionary_rules": [
          ]
        }
      },
      "filter": {
        "ja_search_synonym": {
          "type": "synonym_graph",
          "lenient": false,
          "updateable": false,
          "expand": true,
          "synonyms": [
          ]
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
            "kuromoji_stemmer",
            "ja_search_synonym"
          ]
        }
      }
    }
  }
}
```

検証用なので、レプリカ数 = 0 としている。

リフレッシュインターバル = 1時間としているので、更新の操作後に _refresh を明示する必要がある。
