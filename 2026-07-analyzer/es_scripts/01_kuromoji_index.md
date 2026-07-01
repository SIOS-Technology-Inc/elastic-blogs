# 01. Kuromoji 用インデックスの作成

Kuromoji は Elastic 公式の Japanese analysis plugin です。
Self-Managed では、各ノードに `analysis-kuromoji` を入れて再起動してから使います
（本記事では Dockerfile でインストールします）。

ここでは2つのアナライザーを用意して比較します。

- `kuromoji`：標準のアナライザー（プラグインが提供）。
- `kuromoji_search`：`kuromoji_tokenizer` を `mode: search` にしたカスタムアナライザー。
  長い複合語を検索向けに分解します。

```json
PUT /jp_kuromoji
{
  "settings": {
    "analysis": {
      "tokenizer": {
        "kuromoji_search_tok": {
          "type": "kuromoji_tokenizer",
          "mode": "search"
        }
      },
      "analyzer": {
        "kuromoji_search": {
          "type": "custom",
          "tokenizer": "kuromoji_search_tok",
          "filter": [
            "kuromoji_baseform",
            "kuromoji_part_of_speech",
            "ja_stop",
            "kuromoji_stemmer",
            "lowercase"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "kuromoji"
      },
      "content_search": {
        "type": "text",
        "analyzer": "kuromoji_search"
      }
    }
  }
}
```

補足：

- 標準の `kuromoji` アナライザーには、機能語を除去する
  `kuromoji_part_of_speech` や `ja_stop` などが最初から含まれています。
- 入力は Python 側で NFKC 正規化済みのテキストを使う前提のため、
  ここでは `icu_normalizer` を付けていません。
- 全角・半角をアナライザー側でそろえたい実運用では、
  `icu_normalizer` キャラクターフィルター（nfkc など）を追加する方法もあります。
