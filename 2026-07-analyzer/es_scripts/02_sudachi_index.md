# 02. Sudachi 用インデックスの作成

Sudachi は Elastic 公式ではなく、Works Applications の外部プラグイン
`elasticsearch-sudachi` を使います。

事前確認（重要）：

- 導入したプラグインが、使用中の Elasticsearch バージョンに対応しているか。
  本記事では 3.6.0 系を使います。
  注意：プラグインのアセットは、ES の「パッチ番号まで一致」が必要です。
  3.6.0 には 9.4.2 用アセットが無く、9.4 系の最新は 9.4.1 でした。
  そのため本記事の Docker では 9.4.1 を使っています。
- 実行環境が外部プラグインの導入を許可しているか。
  Elastic Cloud Serverless では外部プラグインを追加できないため、対象外です。
- Sudachi 辞書（system_core.dic など）が配置されているか。
  本記事では Dockerfile で配置します。

ここでは A / B / C の3モードを、それぞれアナライザーとして用意します。

```json
PUT /jp_sudachi
{
  "settings": {
    "index": {
      "analysis": {
        "tokenizer": {
          "sudachi_a_tok": {
            "type": "sudachi_tokenizer",
            "split_mode": "A",
            "discard_punctuation": true
          },
          "sudachi_b_tok": {
            "type": "sudachi_tokenizer",
            "split_mode": "B",
            "discard_punctuation": true
          },
          "sudachi_c_tok": {
            "type": "sudachi_tokenizer",
            "split_mode": "C",
            "discard_punctuation": true
          }
        },
        "analyzer": {
          "sudachi_a": {
            "type": "custom",
            "tokenizer": "sudachi_a_tok",
            "filter": ["sudachi_baseform", "sudachi_part_of_speech", "sudachi_ja_stop"]
          },
          "sudachi_b": {
            "type": "custom",
            "tokenizer": "sudachi_b_tok",
            "filter": ["sudachi_baseform", "sudachi_part_of_speech", "sudachi_ja_stop"]
          },
          "sudachi_c": {
            "type": "custom",
            "tokenizer": "sudachi_c_tok",
            "filter": ["sudachi_baseform", "sudachi_part_of_speech", "sudachi_ja_stop"]
          }
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "content_a": { "type": "text", "analyzer": "sudachi_a" },
      "content_b": { "type": "text", "analyzer": "sudachi_b" },
      "content_c": { "type": "text", "analyzer": "sudachi_c" }
    }
  }
}
```

補足：

- モード A は最小単位（細かい）、C は固有表現などを含む大きい単位、B はその中間です。
- フィルター名やオプション名は、導入したプラグインのバージョンの README で必ず確認してください。
  バージョンによって名前や指定方法が変わることがあります。
- 辞書の場所を明示する必要がある場合は、`resources_path` などの指定を追加します
  （プラグインの README に従ってください）。
- 入力は Python 側で NFKC 正規化済みのテキストを使う前提です。
