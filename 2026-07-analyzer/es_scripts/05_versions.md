# 05. 再現性のためのバージョン情報

「いつ・どのバージョンで測ったか」を残します。
これがあると、さらに1年後に本当に再比較できます。

## Elasticsearch のバージョン

```json
GET /
```

`version.number` を記録します（本記事では 9.4.1）。

## インストール済みプラグインの一覧

```
GET _cat/plugins?v
```

`analysis-kuromoji`、`analysis-icu`、`analysis-sudachi` などのバージョンを記録します。

## アナライザー設定の確認

```json
GET /jp_kuromoji/_settings
```

```json
GET /jp_sudachi/_settings
```

## 記録しておく項目（チェックリスト）

- Elasticsearch のバージョン。
- プラグイン一覧（`GET _cat/plugins?v` の結果）。
- 使用したアナライザー設定（settings JSON）。
- Kuromoji プラグインのバージョン。
- Sudachi プラグインのバージョン。
- Sudachi 辞書のバージョン。
- MeCab 辞書のバージョン。
- Janome / Lindera ライブラリのバージョン。
- Python のバージョン。
- 入力テキスト（データセット）のハッシュ。
- LLM のモデル名。
- LLM へのプロンプト。
- LLM の temperature。
- 実行日。

Python 側のバージョンや辞書情報は、`analyzer_compare/` の実行時に
`results/run_metadata.json` へ自動で書き出します。
