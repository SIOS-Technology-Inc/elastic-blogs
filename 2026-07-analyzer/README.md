# 日本語アナライザー比較（2026年・続編）サンプル

2025年に公開した
「日本語アナライザーの比較（Kuromoji / Sudachi / MeCab / LLM の性能検証）」
の続編で使うサンプル一式です。

## 概要

1年後の視点で、日本語の検索がどう変わったかを確認します。
また、より良い方法でアナライザーを比較し直します。

詳しい手法と、2025年版からの改良点は `METHODOLOGY.md` にまとめています。

## できること

- Elasticsearch 上の Kuromoji（標準・mode: search）と Sudachi（A/B/C）でトークン化。
- Python 側で MeCab / Janome / Lindera を使った事前トークン化（参考）。
- LLM（gpt-oss-120b / GPT-5.5 / Claude）による検索キーワード抽出（参考枠）。
- トークン数、形態素解析器どうしのペアワイズ Jaccard、検索クエリでの動作確認。

## 動作に必要な環境

- Elasticsearch（Docker で起動。本記事は v9.4.1 で確認）。
  ※ Sudachi プラグイン 3.6.0 に合わせて 9.4.1 にしています
  （3.6.0 は 9.4.2 用アセットが無いため）。
- Docker（プラグイン入りの Elasticsearch をビルドして起動）。
- Python 3.11 以上。
- LLM を使う場合は、各 API キー（`.env` に設定）。

外部プラグインについての注意:

- Kuromoji は Elastic 公式プラグインです。
- Sudachi は外部プラグイン（Works Applications）です。
- Elastic Cloud Serverless では外部プラグインを追加できないため、
  Sudachi の実験は Self-Managed などで行ってください。

## 動かし方

### 1. 環境変数の準備

```
cp .env.sample .env
```

`.env` を編集し、パスワードや API キーを設定します。

### 2. Elasticsearch の起動

```
docker compose up -d --build
```

初回はプラグインのインストールと Sudachi 辞書のダウンロードが行われます。

### 3. インデックスの作成と確認

Kibana の Dev Tools（http://localhost:5601）で、
`es_scripts/01` 〜 `05` を順に実行します。

### 4. 比較スクリプトの実行

```
pip install -r requirements.txt
cd analyzer_compare
python compare.py
```

結果は `results/` に出力されます。

## ファイルの説明

| パス | 説明 |
|---|---|
| `METHODOLOGY.md` | 手法と、2025年版からの改良点の宣言 |
| `BLOG.md` | ブログ本文の下書き（日本語） |
| `data/` | テストテキストと説明 |
| `Dockerfile-es01` | Kuromoji + ICU + Sudachi 入りの Elasticsearch |
| `docker-compose.yml` | Elasticsearch / Kibana のコンテナ構成 |
| `.env.sample` | 環境変数のサンプル |
| `requirements.txt` | Python の依存ライブラリ |
| `es_scripts/` | Dev Tools 用のリクエスト集 |
| `analyzer_compare/` | トークン化・クリーニング・比較の Python コード |
| `results/` | 実行結果の出力先 |
