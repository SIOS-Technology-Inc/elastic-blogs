#!/bin/bash
# 投入後に forcemerge して条件をそろえ、サイズとフィールド別内訳を表示する
# 使い方: create_indices.sh と同じ環境変数 (ES_URL, ES_AUTH または ES_API_KEY)
set -e
# 同じフォルダの .env があれば読み込む (.env の値を優先)
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi
: "${ES_URL:?ES_URL を設定してください}"
if [ -n "$ES_API_KEY" ]; then AUTH=(-H "Authorization: ApiKey $ES_API_KEY"); else AUTH=(-u "$ES_AUTH"); fi
[ "$ES_INSECURE" = "1" ] && AUTH+=(-k)
IDX="access-logs-standard,access-logs-logsdb,access-logs-columnar"

echo "== refresh"
curl -s "${AUTH[@]}" -X POST "$ES_URL/$IDX/_refresh" >/dev/null
echo "== forcemerge (数分かかることがあります)"
curl -s "${AUTH[@]}" -X POST "$ES_URL/$IDX/_forcemerge?max_num_segments=1"
echo; echo "== サイズ比較"
curl -s "${AUTH[@]}" "$ES_URL/_cat/indices/access-logs-*?v&h=index,docs.count,store.size,pri.store.size,segments.count&s=index"

echo; echo "== フィールド別のディスク使用量 (inverted_index / doc_values など)"
python3 "$(dirname "${BASH_SOURCE[0]}")/disk_usage_report.py"
