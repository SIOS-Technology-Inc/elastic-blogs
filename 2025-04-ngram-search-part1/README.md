# Elasticsearch でN-gramを利用した検索を行うサンプル

# 1. 概要

https://elastic.sios.jp/blog/n-gram-search-in-elasticsearch-p-1/ にて2025年4月に公開のブログ
「Elasticsearchでの N-gram 検索(Part 1)」で使用したElasticsearch用のリクエストです。

詳細は、リンク先のブログを参照してください。


# 2. ファイルの説明

| 相対ファイルパス | 説明 |
|---|---|
| [./LICENSE](./LICENSE) | ライセンスを記載したファイル |
| ./README.md | このファイル |
| [es_requests/5_create_index.md](es_requests/5_create_index.md) | N-gram 検索の検証用のインデックスの作成リクエスト |
| [es_requests/6_post_docs.md](es_requests/6_post_docs.md) | 検証用のドキュメントの登録リクエスト |
| [es_requests/7_search_without_ngram.md](es_requests/7_search_without_ngram.md) | N-gramを利用しない検索リクエスト |
| [es_requests/8_search_with_ngram.md](es_requests/8_search_with_ngram.md) | N-gramを利用した検索リクエスト |
| [es_requests/9_add_doc.md](es_requests/9_add_doc.md) | 検証用ドキュメントの追加登録リクエスト |

