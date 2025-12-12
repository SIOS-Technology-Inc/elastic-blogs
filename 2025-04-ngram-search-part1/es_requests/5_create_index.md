# N-gram 検索の検証用のインデックスの作成リクエスト

前提条件:

- ICU analysis plugin をインストールしておくこと。
- kuromoji analysis plugin をインストールしておくこと。

```
PUT /ngram_sample_202504
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
          "name": "nfkc",
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
        },
        "ja_ngram_tokenizer": {
          "type": "ngram",
          "min_gram": 2,
          "max_gram": 2,
          "token_chars": [
            "letter",
            "digit"
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
        "ja_ngram_index_analyzer": {
          "type": "custom",
          "char_filter": [
            "ja_normalizer"
          ],
          "tokenizer": "ja_ngram_tokenizer",
          "filter": [
            "lowercase"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "chunk_no": {
        "type": "long"
      },
      "content": {
        "type": "text",
        "analyzer": "ja_kuromoji_index_analyzer",
        "search_analyzer": "ja_kuromoji_index_analyzer",
        "fields": {
          "ngram": {
            "type": "text",
            "analyzer": "ja_ngram_index_analyzer",
            "search_analyzer": "ja_ngram_index_analyzer"
          }
        }
      }
    }
  }
}
```
