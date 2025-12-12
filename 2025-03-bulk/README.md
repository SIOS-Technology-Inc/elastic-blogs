# Bulk API を使った Elasticsearch へのドキュメント一括登録サンプル

# 1. 概要

2025年3月に https://elastic.sios.jp/category/blog/ にて公開予定のブログ「Bulk API （Pythonからのドキュメントの一括登録）」用に作成した簡易アプリケーションです。

## できること

- テキストファイルを読み込んで、1行ずつ Elasticsearch のインデックスへドキュメントを登録する。

## 動作に必要な環境など

- Elastic Cloud （筆者は Enterprise Edition v8.17.3 で動作確認）
- Docker

その他、下記のライブラリは、自動でダウンロードされます。

- Python 3.13
- elasticsearch 8.17.1 (Elasticsearch の Python用のClient)
- python-dotenv 1.0.1

## 制限事項

- エラー処理やセキュリティ対策は十分ではありません。あくまでもサンプルです。

# 2. 動かし方

## 2.1. 準備

### 2.1.1. Elastic Cloud 上での準備

- [デプロイメントの作成](https://elastic.sios.jp/blog/creating-deployment-on-elasticcloud/)

- [日本語用の形態素解析の準備](https://elastic.sios.jp/blog/creating-an-index-suitable-for-japanese/)

- [日本語用の密ベクトルの生成準備](https://elastic.sios.jp/blog/preparing-for-vector-search/)


### 2.1.2. Elasticsearch の Console 上で各スクリプトを実行

下記を Elastic Cloud の Console から実行します。

最後の API Key の実行結果（encodedされた Key）は、次の 2.1.3. で使うのでメモ帳などに一時保存しておきます。

- es_scripts/3_create_synonyms_set.md 同義語セットの作成
- es_scripts/4_create_index.md 書き込み先のインデックスの作成
- es_scripts/5_create_index_mappings.md 書き込み先のインデックスのフィールドの作成
- es_scripts/6_create_ingest_pipeline.md データ取り込み用のパイプラインの作成
- es_scripts/7_create_alias.md エイリアスの作成
- es_scripts/9_create_api_key.md 書き込み用の API Key の作成

### 2.1.3. .env ファイルに動作に必要な情報を記載する。

Elasticsearch endpoint の取得方法は、
2025年3月に公開予定のブログ「Bulk API （Pythonからのドキュメントの一括登録）」
に記載予定です。

write_api_key_encoded には、先ほど取得した、書き込み用の API Key の実行結果を貼り付けます。

```
elasticsearch_endpoint='...'

...

write_api_key_encoded='...'

...
```


## 2.2 ビルド ～ コンテナ内での bash の実行

### 2.2.1. ビルド

docker-compose.yml があるディレクトリで下記を実行する。

```docker compose build```

### 2.2.2. コンテナの起動

```docker compose up -d```

### 2.2.3. コンテナ内で bash を実行

```docker exec -it bulk_sample_202503 /bin/bash```

（"bulk_sample_202503"はコンテナ名）


## 2.3. Elasticsearch へのデータ登録

さきほど実行開始した bash から以下のコマンドを実行する。

### 2.3.1. チャンク済のデータをインデックスへ登録する。

チャンク済のデータを、es_consts.pyで指定したインデックス("kakinosuke")へ登録する。

```python src/bulk_from_txt.py data/kakinosuke.txt_chunked.txt```

正常終了すると、指定したインデックス（"kakinosuke"）に、ドキュメントが登録されます。


# 3. ファイルの説明

| 相対ファイルパス | 説明 |
|---|---|
| ./.env | 接続に必要な API Key などを記載するファイル |
| ./docker-compose.yml | Docker の Compose ファイル |
| ./Dockerfile | Docerfile |
| ./License.txt | ライセンスを記載したファイル |
| ./README.md | このファイル |
| ./requirements.txt | 動作に必要なライブラリの指定ファイル |
| data/kakinosuke.txt_chunked.txt | 桃太郎を改変した柿之助をチャンキング処理したファイル |
| data/README.md | kakinosuke.txt_chunked.txt の説明ファイル |
| es_scripts/*.md | Elasticsearch用の各種設定スクリプト |
| src/bulk_from_txt.py | テキストファイルを読み込んで、Elasticsearch へ データ登録するプログラム |
| src/common/setup_logger.py | ロガーを設定する関数 |
| src/elastic/es_consts.py | Elasticsearch関連の定数定義ファイル |
| src/elastic/es_func.py | Elasticsearch関連の関数を集めたファイル |
