# 03. _analyze によるトークンの確認

`_analyze` API で、各アナライザーがどうトークンを分けるかを確認します。
ここでは Text 1（ロキソニン）を例にします。
Text 2（アセトアミノフェン）も、`text` を差し替えて同様に実行してください。

入力は NFKC 正規化済みのテキストを使う前提です。

## Kuromoji（標準）

```json
POST /jp_kuromoji/_analyze
{
  "analyzer": "kuromoji",
  "text": "ロキソニン錠の説明書ですね。ロキソニンは、解熱鎮痛作用のある非ステロイド性抗炎症薬（NSAIDs）で、痛みや発熱、炎症を抑える効果があります。"
}
```

## Kuromoji（mode: search のカスタム）

```json
POST /jp_kuromoji/_analyze
{
  "analyzer": "kuromoji_search",
  "text": "ロキソニン錠の説明書ですね。ロキソニンは、解熱鎮痛作用のある非ステロイド性抗炎症薬（NSAIDs）で、痛みや発熱、炎症を抑える効果があります。"
}
```

## Sudachi（A / B / C）

```json
POST /jp_sudachi/_analyze
{
  "analyzer": "sudachi_a",
  "text": "ロキソニン錠の説明書ですね。ロキソニンは、解熱鎮痛作用のある非ステロイド性抗炎症薬（NSAIDs）で、痛みや発熱、炎症を抑える効果があります。"
}
```

`sudachi_b`、`sudachi_c` も `analyzer` を変えて同様に実行します。

## 見るポイント

- 専門語が1語のまま残るか、細かく分かれるか。
  例：`非ステロイド性抗炎症薬`、`解熱鎮痛`、`アセトアミノフェン`。
- 英字の略語が保持されるか。例：`NSAIDs`。
- 数値と単位がどう分かれるか。例：`300mg`、`300〜500mg`。
- 同じ語が、アナライザーごとに違う形（表層形／基本形）になっていないか。

トークンの一覧と件数は、`analyzer_compare/` の Python スクリプトでも自動取得できます。
