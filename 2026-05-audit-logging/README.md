# Audit Logging サンプル

## 概要

https://elastic.sios.jp/category/blog/ で公開予定のブログ
「Elasticsearch Audit Logging 解説：セキュリティ監視とコンプライアンスのための第一歩」
で使用するサンプルアプリケーションです。

## 実現できること

- オンプレミス環境の Elasticsearch ノードの Audit Log の出力
  - 発行したクエリーの出力も含む

## Audit Log とは

Elastic Audit Log は、Elasticsearch クラスターの監査ログです。

参考URL

- https://www.elastic.co/docs/deploy-manage/security/logging-configuration/security-event-audit-logging

- https://www.elastic.co/docs/reference/elasticsearch/configuration-reference/auding-settings

- https://www.elastic.co/docs/reference/elasticsearch/elasticsearch-audit-events

- https://qiita.com/nobuhikosekiya/items/ba0a1a004fa4b3b1d856


## サンプルの内容

- Elasticsearch 環境
  - docker-compose.yml, .env.sample, Dockerfile-es01
    - オンプレミス Elasticsearch をコンテナとして動作させます。
  - log4j2.properties
    - Audit Log をファイルに出力します。

## 動作確認環境

- Docker 実行環境  
  - 筆者は Windows 上の Rancher Desktop 1.22.2 で動作確認

- オンプレミス Elasticsearch: v9.4.0 (Trial License)
  - 自動でダウンロードされます。
  - 本番環境で Audit Logging 機能を利用する場合は Enterprise License が必要です。

## ファイルの説明

| ファイル | 説明 | 備考 |
|---|---|---|
| [.env.sample](./.env.sample) | 環境変数のテンプレート | .env にコピーして使用 |
| [docker-compose.yml](./docker-compose.yml) | Elasticsearch 本体の構成 | Data : 1 node, Kibana :  1 node <br> クエリーの内容を含む Audit Log を出力する。(*1) |
| [Dockerfile-es01](./Dockerfile-es01) | Elasticsearch用カスタム Dockerfile | カスタマイズした log4j2.properties ファイルをコピーして使用します。 |
| [log4j2.properties](./log4j2.properties) | Elasticsearch用ログファイル出力設定ファイル | /usr/share/elasticsearch/logs/クラスタ名_audit.json に Audit Log を出力するための設定ファイル。(*2) |

(*1) Audit Log の取得用に下記の設定を追加しています。

```
      - xpack.security.audit.enabled=true
      - xpack.security.audit.logfile.events.emit_request_body=true
      - xpack.security.audit.logfile.events.include=_all
```

(*2) Audit Log をファイルに出力するために下記の設定を追加しています。

```
# appender.audit_rolling.type = Console
appender.audit_rolling.type = RollingFile
appender.audit_rolling.name = audit_rolling
appender.audit_rolling.fileName = ${sys:es.logs.base_path}${sys:file.separator}${sys:es.logs.cluster_name}_audit.json
appender.audit_rolling.filePattern = ${sys:es.logs.base_path}${sys:file.separator}${sys:es.logs.cluster_name}_audit-%d{yyyy-MM-dd}-%i.json.gz
appender.audit_rolling.policies.type = Policies
appender.audit_rolling.policies.time.type = TimeBasedTriggeringPolicy
appender.audit_rolling.policies.time.interval = 1
appender.audit_rolling.policies.time.modulate = true
appender.audit_rolling.policies.size.type = SizeBasedTriggeringPolicy
appender.audit_rolling.policies.size.size = 10MB
appender.audit_rolling.strategy.type = DefaultRolloverStrategy
# appender.audit_rolling.strategy.fileIndex = nomax
appender.audit_rolling.strategy.fileIndex = 10
```

## セットアップ手順

### 1. パスワードなどの設定

.env.sample を .env にコピーし、パスワードや暗号化キー、メモリサイズを編集します。

```
cp .env.sample .env
```

主な設定項目

- CLUSTER_NAME : 監視画面に表示されるクラスタ名

- ELASTIC_PASSWORD : 任意のパスワード

- KIBANA_PASSWORD : 任意のパスワード

- SAVEDOBJECTS_ENCRYPTIONKEY: 32文字以上のランダムな文字列

- ES01_MEM_LIMIT : Elasticsearch コンテナに割り当てるメモリの上限サイズ

- KB_MEM_LIMIT : Kibana コンテナに割り当てるメモリの上限サイズ

### 2. コンテナの起動
  
Rancher Desktop 等の Docker ランタイムが起動していることを確認し、以下を実行します。

```
docker-compose up -d --build
```

オンプレミスの Elasticsearch 9.4.0 のダウンロードが行われるため、しばらく時間がかかります。

### 3. 各種アクセス

#### 3.1. 存在しないユーザーでのログイン失敗

```
curl -X GET -u dummy:dummy --cacert ./certs/ca/ca.crt https://localhost:9200/?pretty
```

#### 3.2. 不正なパスワードでのログイン失敗

```
curl -X GET -u elastic:dummy --cacert ./certs/ca/ca.crt https://localhost:9200/?pretty
```

#### 3.3. インデックスの作成

```
curl -X PUT -u elastic:password --cacert ./certs/ca/ca.crt "https://localhost:9200/my_index/_doc/1?pretty" -d '{ \"user\": \"user1\", \"message\": \"Elasticsearch curl test\" }'
```

#### 3.4. インデックスの検索

```
curl -X POST -u elastic:password --cacert ./certs/ca/ca.crt "https://localhost:9200/my_index/_search?pretty" -d '{ \"query\": { \"match\": { \"message\": \"Elasticsearch\" } } }'
```

### 4. ログファイルの確認

```
docker exec -it es01コンテナ名 /bin/bash
```

```
cd /usr/share/elasticsearch/logs
ls -l
```

クラスタ名_audit.json ファイルが出力されていることを確認します。

```
-rw-rw-r-- 1 elasticsearch elasticsearch 3753228 May  7 01:13 docker-cluster-audit-logging-202605_audit.json
-rw-rw-r-- 1 elasticsearch elasticsearch   58058 May  7 01:10 gc.log
```

ログファイルの内容の確認

```
cat クラスタ名_audit.json
```

大量にログが表示されるので、一旦、ローカルにコピーするなど、見やすい環境で内容を確認してください。


### 5. 出力されるログの例

#### 5.1. 未知のユーザーによるアクセス、または、不正なパスワードによるアクセス

出力ログ（抜粋）

```
{
  "type":"audit",
  "timestamp":"2026-05-07T01:22:22,842+0000",
  "event.action":"authentication_failed",
  "user.name":"dummy",
  "origin.address":"192.168.143.2:35134",
  "url.path":"/",
  "request.method":"GET"
}
```

#### 5.2. 権限のないインデックスへのアクセス

出力ログ（抜粋）

```
{
  "type":"audit",
  "event.action":"access_denied",
  "user.name":"guest1",
  "action":"indices:data/read/search",
  "indices":["kibana_sample_data_logs"]
}
```

#### 5.3. 検索クエリーの記録

出力ログ（抜粋）

```
{
  "event.action":"authentication_success",
  "user.name":"elastic",
  "url.path":"/kibana_sample_data_logs/_search",
  "request.body":"{\"query\":{\"match\":{\"geo.dest\":\"CN\"}}}"
}
```

