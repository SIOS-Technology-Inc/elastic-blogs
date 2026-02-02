# OpenTelemetry を使った Elastic Observability サンプルアプリケーション

## 1. 概要

https://elastic.sios.jp/category/blog/ で公開予定のブログ
「OpenTelemetry を使って Elastic Observability にログ、メトリクス、トレースを取り込んでみよう。」
で使用するサンプルアプリケーションです。

このサンプルアプリでは、Elastic Distribution of OpenTelemetry (EDOT) Collector を使って、ログ、メトリクス、トレースを Elasticsearch に取り込みます。

## 2. できること

- EDOT Collector を動作させているホストの /var/log/*.log を取得し、Kibana の Discovery で表示する。
- EDOT Collector を動作させているホストの各種メトリクス (CPU, Memory, Network など) を取得し、Kibana の Dashboard で表示する。
- Python アプリのトレースを取得し、Kibana の Applications で表示する。

## 3. 動作に必要な環境

- Docker 実行環境  
  ※筆者は Windows 上の Rancher Desktop 1.20.1 で動作確認

その他、下記は自動でダウンロードされます。

- Elasticsearch 9.2.4
- Kibana 9.2.4
- Python 3.14

## 4. 動かし方

https://elastic.sios.jp/category/blog/ を参照してください。

## 5. ファイルの説明

| 相対ファイルパス | 説明 |
|---|---|
| ./README.md | このファイル |
| [app/docker-compose-es-kibana-python.yml](app/docker-compose-es-kibana-python.yml) | Docker Compose ファイル |
| [app/.env.sample](app/.env.sample) | .env のサンプルファイル |
| [app/python/Dockerfile](app/python/Dockerfile) | Python 実行用の Dockerfile |
| [app/python/otel.yml.sample](app/python/otel.yml.sample) | otel.yml のサンプルファイル |
| [app/python/src/test.py](app/python/src/test.py) | テスト用の Python ソースコード |
