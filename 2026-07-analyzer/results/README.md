# results — 実行結果の出力先

`analyzer_compare/compare.py` を実行すると、ここに次のファイルが生成されます。

- `text1_loxonin_tokens.json` — Text 1 の各アナライザーのトークンと集計。
- `text2_medical_tokens.json` — Text 2 の各アナライザーのトークンと集計。
- `summary.md` — 人が読むためのサマリー（トークン数、専門用語の保持、ペアワイズ Jaccard、LLM の抽出キーワード）。
- `run_metadata.json` — 再現性のためのバージョン情報・実行日・データセットのハッシュ・LLM 設定。
- `search_results.md` / `search_results.json` — 検索クエリでの動作確認（どのアナライザーが期待文書を拾えたか）。

これらは実行のたびに上書きされます。
ブログ本文（`BLOG.md`）の表は、ここで得た数値を貼り付けて完成させます。
