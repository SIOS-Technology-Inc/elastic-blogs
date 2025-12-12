# ElasticsearchでのN-gram検索を利用したサンプルアプリケーション

## 概要

https://elastic.sios.jp/category/blog/ で公開予定のブログ
「Elasticsearch での N-gram 検索 (Part 2) 医薬品マスタの検索」
で使用したサンプルアプリケーションです。

医薬品名を2文字以上入力することで医薬品の候補を絞り込みます。

## できること

1. N-gram 検索を使って医薬品検索を行うことができます。
   
   ※医薬品名は、kuromoji が知らない単語が多いですが、ユーザー辞書登録を行うことなく検索することが可能です。


## 動作に必要な環境など

- Elasticsearch (筆者は Elastic Cloud 8.18.0 で動作確認)
- Docker (筆者は Rancher Desktop 1.18.2 で動作確認)

その他、下記は、自動でダウンロードされます。

- Python 3.13
- elasticsearch 8.18.1 (Elasticsearch の Python用のClient)
- flask 3.1.0
- python-dotenv 1.0.1

## 動かし方

### 事前準備

1. 医薬品マスタの登録

医薬品マスタの CSV ファイルを加工して、Elasticsearch へアップロードし、インデックスに登録します。

その際、Index settings と mappings を指定します。

詳細は、前述のブログを参照してください。


### ビルド ～ Container との接続

1. ビルド

docker-compose.yml があるディレクトリへ移動します。

```
cd flask_app
```

下記を実行します。

```docker compose build```

2. コンテナの起動

```docker compose up -d```

3. コンテナとの接続

```docker exec -it search_with_ngram_sample_202505 /bin/bash```

("search_with_ngram_sample_202505"はコンテナ名)


### 医薬品検索アプリの開始

```python run.py```

Web Browser から http://localhost:5000/ にアクセスして、医薬品検索を行います。

※停止ボタンは用意していないので、停止させたい場合は、Ctrl+C を押すなどの処置を行ってください。


### 実際の動作

下記の動画のような動きになります。

<a href="./search_medicine_20250501.mp4">search_medicine_20250501.mp4</a>

## ファイルの説明

| 相対ファイルパス | 説明 |
|---|---|
| ./README.md | このファイル |
| ./search_medicine_20250501.mp4 | サンプル動画 |
| csv/README.md | csv についての説明 |
| csv/y_20250415.csv | オリジナルの医薬品マスタ（20250415版） |
| csv/y_20250415_col2.csv | 医薬品コードと医薬品名のみに絞った医薬品マスタ(Shift_JIS) |
| csv/y_20250415_col2_utf8.csv | 医薬品コードと医薬品名のみに絞った医薬品マスタ(utf8) |
| es_requests/README.md | Elasticsearch で実行するリクエストの説明 |
| es_requests/01_create_index_settings.md | CSV ファイルのアップロード時に index の settings に張り付けるべき内容 |
| es_requests/02_create_index_mappings_with_ngram.md | CSV ファイルのアップロード時に index の mappings に張り付けるべき内容 |
| es_requests/03_create_alias.md | インデックスに対するエイリアスの作成リクエスト |
| es_requests/04_search_template_with_ngram.md | N-gram検索を利用した検索テンプレートの作成リクエスト |
| es_requests/05_access_key.md | インデックスの読み取り用の Access Key の作成リクエスト |
| flask_app/.env | 接続に必要な API Key などを記載するファイル |
| flask_app/docker-compose.yml | Docker の Compose ファイル |
| flask_app/Dockerfile | Docerfile |
| flask_app/requirements.txt | 動作に必要なライブラリの指定ファイル |
| flask_app/run.py | 検索アプリの開始用スクリプト |
| flask_app/app/common/env_consts.py | .env ファイル関連の定数ファイル |
| flask_app/app/common/load_env_wrapper.py | .env ファイル読み込み関数ファイル |
| flask_app/app/common/setup_logger.py | ロガーの設定関数ファイル |
| flask_app/app/elastic/es_consts.py | Elasticsearch 関連の定数ファイル |
| flask_app/app/elastic/es_func.py | Elasticsearch 関連の関数ファイル |
| flask_app/app/static/css/style.css | スタイルシート |
| flask_app/app/static/js/scripts.js | JavaScript関数を集めたファイル |
| flask_app/app/templates/index.html | テンプレート HTML ファイル |
| flask_app/app/app.py | Flask用アプリの本体 |

