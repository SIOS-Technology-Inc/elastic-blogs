# Reindexの実行

Reindex API を使って、既存の kakinosuke_202503 インデックスから kakinosuke_202504 インデックスへドキュメントをコピーします。

```
POST _reindex?refresh=true
{
  "source": {
    "index": "kakinosuke_202503",
    "_source": [ "chunk_no", "content" ]
  },
  "dest": {
    "index": "kakinosuke_202504",
    "pipeline": "japanese-text-embeddings"
  }
}
```

Reindex を行う際に、以下の指定を行っています。

- "refresh=true" -> Reindex 終了後に refresh を行います。

- "_source" : [ "chunk_no", "content" ] -> コピー対象のフィールド名を明記しておきます。すべてコピーする場合には省略可能ですが、今回はわかりやすいよう、あえて明記しています。

- "pipeline": "japanese-text-embeddings" -> 文字列を再登録する際に、ベクトルを生成します。コピー元の kakinosuke_202501 インデックスでは、密ベクトルを _source に保持していないのでコピーすることができません。Reindex 実行時に、再度、pipeline を通すことで、密ベクトルを再作成します。

※ "japanese-text-embeddings" パイプラインは、[ベクトル検索の準備](https://elastic.sios.jp/blog/preparing-for-vector-search/) の回で登録した、密ベクトル生成用のパイプラインです。
