# 「 Markdown 文書のための再帰チャンキング入門 — Elasticsearch での実践と比較」のサンプルスクリプト


## 1. 概要

https://elastic.sios.jp/category/blog/ で公開予定のブログ
「Markdown 文書のための再帰チャンキング入門 — Elasticsearch での実践と比較」
で使用するサンプルスクリプトです。

このサンプルでは、`ir_report_2024_chunk_recursive` インデックスに対しドキュメントを登録しますが、
その際に、recursive chunking を使ってチャンキングと密ベクトル生成を行います。


## 2. 動作に必要な環境

- Elasticsearch（Platinum License 以上）  
  ※筆者は Elasticsearch 9.2.2 Enterprise License で動作確認

  - Machine Learning node
    - .multilingual-e5-small_linux-x86_64 モデルをデプロイしておく必要があります。

## 3. ファイルの説明

| 相対ファイルパス | 説明 |
|---|---|
| ./README.md | このファイル |
| [input_data/ir_report_20250328.md](input_data/ir_report_20250328.md) | 入力データ |
| [plugins/plugins.md](plugins/plugins.md) | このサンプルを動かすのに必要なプラグイン |
| [es_requests/01_create_inference.md](es_requests/01_create_inference.md) | Inference Endpoint の作成リクエスト |
| [es_requests/02_create_index_settings.md](es_requests/02_create_index_settings.md) | インデックスの作成リクエスト |
| [es_requests/03_create_index_mappings.md](es_requests/03_create_index_mappings.md) | インデックスへのフィールドの作成リクエスト |
| [es_requests/04_post_doc.md](es_requests/04_post_doc.md) | インデックスへのドキュメントの登録リクエスト |
| [es_requests/05_search.md](es_requests/05_search.md) | 検索リクエスト |


