# ユーザー辞書登録を行ったインデックスの作成

```
PUT /kakinosuke_202504
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
          "discard_compound_token": true,
          "user_dictionary_rules": [
            "柿之助,柿之助,カキノスケ,カスタム名詞"
          ]
        }
      },
      "filter": {
        "ja_search_synonym": {
          "type": "synonym_graph",
          "synonyms_set": "kakinosuke_synonyms_set",
          "updateable": true
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
  },
  "mappings": {
    "dynamic": false,
    "_source": {
      "excludes": [
        "text_embedding.*"
      ]
    },
    "properties": {
      "chunk_no": {
        "type": "integer"
      },
      "content": {
        "type": "text",
        "analyzer": "ja_kuromoji_index_analyzer",
        "search_analyzer": "ja_kuromoji_search_analyzer"
      },
      "text_embedding": {
        "properties": {
          "model_id": {
            "type": "keyword",
            "ignore_above": 256
          },
          "predicted_value": {
            "type": "dense_vector",
            "dims": 384
          }
        }
      }
    }
  }
}
```

user_dictionary に「柿之助」を登録します。
