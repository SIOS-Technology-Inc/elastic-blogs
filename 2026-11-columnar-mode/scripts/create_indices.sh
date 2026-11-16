#!/bin/bash
# 3つの index (standard / logsdb / logsdb_columnar) を同じマッピングで作る
#
# 使い方 (Elastic Cloud Hosted):
#   export ES_URL=https://xxxx.es.asia-northeast1.gcp.elastic-cloud.com:443
#   export ES_API_KEY="xxxx"                 # Kibana で作った API キーの encoded 値
#   # export ES_AUTH="elastic:パスワード"     # パスワード認証を使う場合はこちら
#   bash create_indices.sh            # 作成
#   bash create_indices.sh --delete   # 削除 (やり直すとき)
set -e
# 同じフォルダの .env があれば読み込む (.env の値を優先)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi
: "${ES_URL:?ES_URL を設定してください (例: http://localhost:9200)}"

if [ -n "$ES_API_KEY" ]; then
  AUTH=(-H "Authorization: ApiKey $ES_API_KEY")
else
  AUTH=(-u "$ES_AUTH")
fi
# 自己署名証明書 (ローカルの Docker 環境など) のときは ES_INSECURE=1 を設定する
[ "$ES_INSECURE" = "1" ] && AUTH+=(-k)

if [ "$1" = "--delete" ]; then
  curl -s "${AUTH[@]}" -X DELETE "$ES_URL/access-logs-standard,access-logs-logsdb,access-logs-columnar?ignore_unavailable=true"
  echo; echo "deleted"; exit 0
fi

MAPPINGS='{
  "properties": {
    "@timestamp":                { "type": "date" },
    "http.request.method":       { "type": "keyword" },
    "http.response.status_code": { "type": "integer" },
    "http.response.bytes":       { "type": "long" },
    "client.ip":                 { "type": "ip" },
    "url.path":                  { "type": "keyword" },
    "duration_ms":               { "type": "float" },
    "service.name":              { "type": "keyword" },
    "service.environment":       { "type": "keyword" },
    "message":                   { "type": "text" }
  }
}'

create() {
  local name=$1 settings=$2
  echo "== create $name"
  curl -s "${AUTH[@]}" -X PUT "$ES_URL/$name" -H 'Content-Type: application/json' \
    -d "{\"settings\": $settings, \"mappings\": $MAPPINGS}"
  echo
}

# 1. 通常モード (比較の基準)
create access-logs-standard '{
  "number_of_shards": 1, "number_of_replicas": 0
}'

# 2. logsdb モード
create access-logs-logsdb '{
  "mode": "logsdb",
  "number_of_shards": 1, "number_of_replicas": 0,
  "sort.field": ["service.name", "@timestamp"],
  "sort.order": ["asc", "desc"]
}'

# 3. Columnar モード (検証対象)
create access-logs-columnar '{
  "mode": "logsdb_columnar",
  "number_of_shards": 1, "number_of_replicas": 0,
  "sort.field": ["service.name", "@timestamp"],
  "sort.order": ["asc", "desc"]
}'

echo "== 確認"
curl -s "${AUTH[@]}" "$ES_URL/_cat/indices/access-logs-*?v&h=index,health,status,pri,rep,docs.count&s=index"
