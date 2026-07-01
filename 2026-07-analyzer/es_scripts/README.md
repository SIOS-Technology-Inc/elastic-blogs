# es_scripts — Elasticsearch 側のスクリプト

Kibana の Dev Tools（Console）に貼り付けて実行する想定のリクエスト集です。

実行順序の目安：

1. `01_kuromoji_index.md` — Kuromoji 用インデックスの作成（標準 `kuromoji` と `mode: search` のカスタム）。
2. `02_sudachi_index.md` — Sudachi 用インデックスの作成（A / B / C モード）。外部プラグインが必要です。
3. `03_analyze.md` — `_analyze` API で各アナライザーのトークンを確認。
4. `04_search_tests.md` — 少数の文書を登録し、検索クエリで「期待する文書が拾えるか」を確認。
5. `05_versions.md` — 再現性のためのバージョン情報の取得。

注意：

- Kuromoji は Elastic 公式プラグイン、Sudachi は外部プラグインです。
  詳しくは、リポジトリ直下の `METHODOLOGY.md` を参照してください。
- 入力テキストは、比較の公平性のため Python 側で NFKC 正規化したものを使う想定です。
  詳細は `analyzer_compare/` を参照してください。
- Sudachi プラグインのオプション名は、導入したバージョン（本記事では 3.6.0 系）の
  README で必ず確認してください。バージョンによって変わることがあります。
