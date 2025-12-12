# Create index mapping

```
PUT /dls_sample_202507/_mapping
{
  "properties": {
    "content": {
      "type": "text"
    },
    "_allow_access_control": {
      "type": "text",
      "index_options": "freqs",
      "analyzer": "iq_text_base",
      "fields": {
        "enum": {
          "type": "keyword",
          "ignore_above": 2048
        }
      }
    }
  }
}
```

## フィールドの説明

| フィールド名 | フィールドタイプ | 説明 |
|---|---|---|
| content | text | ドキュメントの本文 |
| _allow_access_control | text | このドキュメントを参照可能なユーザー名またはグループ名の集合 |
| _allow_access_control.enum | keyword | このドキュメントを参照可能なユーザー名またはグループ名（単一要素） |

※あくまでも Document Level Security の動作を確認するためのインデックスなので、
登録内容の形態素解析などは省略しています。

