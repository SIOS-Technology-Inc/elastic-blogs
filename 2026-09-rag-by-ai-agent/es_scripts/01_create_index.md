# インデックスの作成

```
PUT /kakinosuke_202609/
{
  "settings": {
    "index": {
      "mode": "vectordb_document",
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
            "柿之助,柿之助,カキノスケ,カスタム名詞"
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

※テスト用なので、number_of_replicas : 0 としています。
