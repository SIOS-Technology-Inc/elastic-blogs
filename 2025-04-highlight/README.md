# Elasticsearch でハイライト表示を行うサンプル

# 1. 概要

https://elastic.sios.jp/blog/highlighting-search-results-in-elasticsearch/ にて2025年4月に公開のブログ
「Elasticsearch での検索結果のハイライト表示」用に作成した簡易アプリケーションです。

## できること

- Elasticsearch でハイブリッド検索（キーワード検索＋密ベクトル検索）を行い、マッチした箇所をハイライト表示する。
- ハイライト表示する / しない を切り替えられる。

## 動作に必要な環境など

- Elastic Cloud （筆者は Enterprise Edition v8.17.3 で動作確認）
- Docker

その他、下記のライブラリは、自動でダウンロードされます。

- Python 3.13
- elasticsearch 8.17.2 (Elasticsearch の Python用のClient)
- streamlit 1.42.2
- python-dotenv 1.0.1

## 制限事項

- エラー処理やセキュリティ対策は十分ではありません。あくまでもサンプルです。

# 2. 動かし方

## 2.1. 準備

### 2.1.1. Elastic Cloud 上での準備

- [デプロイメントの作成](https://elastic.sios.jp/blog/creating-deployment-on-elasticcloud/)

- [日本語用の形態素解析の準備](https://elastic.sios.jp/blog/creating-an-index-suitable-for-japanese/)

- [日本語用の密ベクトルの生成準備](https://elastic.sios.jp/blog/preparing-for-vector-search/)

- [ドキュメントの登録]()


### 2.1.2. Elasticsearch の Console 上で各スクリプトを実行

下記を Elastic Cloud の Console から実行します。

最後の API Key の実行結果（encodedされた Key）は、次の 2.1.3. で使うのでメモ帳などに一時保存しておきます。

- es_scripts/4_search_template.md 検索テンプレート（ハイライト指定可）の作成
- es_scripts/5_create_api_key.md 読み取り用の API Key の作成

### 2.1.3. .env ファイルに動作に必要な情報を記載する。

Elasticsearch endpoint の取得方法は、2025年3月に公開したブログ
 [Bulk API （Pythonからのドキュメントの一括登録）](https://elastic.sios.jp/blog/bulk-api-python/) に記載済です。

read_api_key_encoded には、先ほど取得した、読み取り用の API Key の実行結果(encodedの値)を貼り付けます。

```
elasticsearch_endpoint='...'

...

read_api_key_encoded='...'

...
```


## 2.2 ビルド ～ コンテナ内での bash の実行

### 2.2.1. ビルド

docker-compose.yml があるディレクトリで下記を実行する。

```docker compose build```

### 2.2.2. コンテナの起動

```docker compose up -d```

### 2.2.3. コンテナ内で bash を実行

```docker exec -it highlight_sample_202504 /bin/bash```

（"highlight_sample_202504"はコンテナ名）


## 2.3. 検索アプリの開始

さきほど実行開始した bash から以下のコマンドを実行する。

```
streamlit run src/app.py
```

### 2.4. Web Browser からのアクセス

Web Browser (Chrome など) から
https://localhost:8501
へアクセスします。

左側のラジオボタンで、ハイライト表示する / しない を切り替えることが可能です。

ハイライト表示する：いいえ　の検索を行った場合のサンプル画面

<img src="./highlight-no-sample.png">


ハイライト表示する：はい　の検索を行った場合のサンプル画面

<img src="./highlight-yes-sample.png">

「柿」「助」「おばあさん」にマッチした部分が強調されて表示されます。

（この時点では、「柿之助」が「柿」と「助」に分解されてマッチングが行われています。
今後、「柿之助」をマッチさせるためのブログを公開予定です。）

# 3. ファイルの説明

| 相対ファイルパス | 説明 |
|---|---|
| ./.env | 接続に必要な API Key などを記載するファイル |
| ./docker-compose.yml | Docker の Compose ファイル |
| ./Dockerfile | Docerfile |
| ./LICENSE | ライセンスを記載したファイル |
| ./README.md | このファイル |
| ./requirements.txt | 動作に必要なライブラリの指定ファイル |
| ./highlight-no-sample.png | ハイライト表示する:いいえ のサンプル画面 |
| ./highlight-yes-sample.png | ハイライト表示する:はい のサンプル画面 |
| es_scripts/*.md | Elasticsearch用の各種設定スクリプト |
| src/app.py | 検索アプリの本体 |
| src/common/load_env_wrapper.py | .env の内容を読み取る関数 |
| src/common/setup_logger.py | ロガーを設定する関数 |
| src/elastic/es_consts.py | Elasticsearch関連の定数定義ファイル |
| src/elastic/es_func.py | Elasticsearch関連の関数を集めたファイル |
| tests/elastic/test_es_func.py | es_func.py 用のテストコード |
