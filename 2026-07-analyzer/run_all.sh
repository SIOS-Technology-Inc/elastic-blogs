#!/usr/bin/env bash
#
# このファイルは「全部まとめて実行する」ためのスクリプト（手順書を自動化したもの）。
# 1行ずつ手で打たなくても、bash run_all.sh だけで最初から最後まで通せる。
#
# 流れ:
#   0) .env が無ければ .env.sample から作る
#   1) Elasticsearch を Docker で起動（プラグイン導入込み・Kibana は起動しない）
#   2) Elasticsearch の起動を待つ
#   3) Python 仮想環境 (.venv) を用意（macOS の externally-managed 対策）
#   4) 依存をインストール
#   5) インデックスを作成
#   6) 比較を実行（結果は results/ に出力）
#
# 使い方:
#   1. .env を用意し、EIS の設定（EIS_ES_URL / EIS_API_KEY / EIS_COMPLETION_INFERENCE_IDS）を記入
#   2. bash run_all.sh
#
# set -euo pipefail = 失敗を早めに検知するための安全設定。
#   -e: コマンドが失敗したら、その場で止まる。
#   -u: 未定義の変数を使ったらエラーにする。
#   -o pipefail: パイプ（|）の途中で失敗しても見逃さない。
set -euo pipefail
# このスクリプトがある場所へ移動する（どこから実行しても同じ場所で動くように）。
# "$0" はスクリプト自身のパス、dirname はそのフォルダ部分。
cd "$(dirname "$0")"

# 0) .env が無ければ .env.sample からコピー
# [ ! -f .env ] は「.env というファイルが無ければ」という条件。
if [ ! -f .env ]; then
  echo "0) .env が無いので .env.sample から作成します（API キーなどは後で編集してください）"
  cp .env.sample .env
fi

# .env を読み込む（ES_URL など）
# set -a の間に source すると、.env の各行が「環境変数」として自動でエクスポートされる。
set -a
# shellcheck disable=SC1091
source .env
set +a
# ES_URL が未設定なら、既定値（ローカル）を使う。:- は「無ければこの値」の意味。
ES_URL="${ES_URL:-http://localhost:9201}"

# 1) Elasticsearch を起動（Kibana は不要なので es01 のみ）
echo "1) Elasticsearch を起動します（初回はプラグイン導入で数分かかります）"
# -d: バックグラウンド起動、--build: Dockerfile から作り直す、es01: そのサービスだけ。
docker compose up -d --build es01

# 2) Elasticsearch の起動を待つ
# 起動直後はまだ応答しないので、応答するまで5秒おきに最大60回（=5分）試す。
echo "2) Elasticsearch の起動を待ちます: ${ES_URL}"
for i in $(seq 1 60); do
  # curl で ES に接続できたら（成功したら）ループを抜ける。
  if curl -s "${ES_URL}" >/dev/null 2>&1; then
    echo "   -> Elasticsearch が応答しました"
    break
  fi
  echo "   ... 待機中 (${i}/60)"
  sleep 5
done

# 3) Python 仮想環境を用意（Homebrew の Python は直接 pip できないため）
# 仮想環境 (.venv) = このプロジェクト専用の、隔離された Python 置き場。
# システム側を汚さずにライブラリを入れられる。
echo "3) Python 仮想環境 (.venv) を用意します"
if [ ! -d .venv ]; then
  # 使える python コマンドを、新しい順に探す。
  PYTHON_FOR_VENV=""
  for candidate in python3.12 python3.11 python3.10 python3; do
    # command -v ... で「そのコマンドが存在するか」を確認する。
    if command -v "${candidate}" >/dev/null 2>&1; then
      PYTHON_FOR_VENV="${candidate}"
      break
    fi
  done
  # 1つも見つからなければ、案内を出して終了する（exit 1 = 失敗終了）。
  if [ -z "${PYTHON_FOR_VENV}" ]; then
    echo "Python 3.10 以上が必要です。Python をインストールしてから再実行してください。"
    exit 1
  fi
  # 見つかった python で仮想環境を作る。
  "${PYTHON_FOR_VENV}" -m venv .venv
fi
# 以降は、この仮想環境の python を使う。
VENV_PY=".venv/bin/python"

# 4) 依存をインストール
echo "4) 依存をインストールします"
"${VENV_PY}" -m pip install --upgrade pip
"${VENV_PY}" -m pip install -r requirements.txt

# 5) インデックスを作成
echo "5) インデックスを作成します"
"${VENV_PY}" analyzer_compare/setup_indices.py

# 6) 比較を実行
echo "6) 比較を実行します"
"${VENV_PY}" analyzer_compare/compare.py

# 7) 検索クエリでの動作確認
echo "7) 検索クエリでの動作確認を実行します"
"${VENV_PY}" analyzer_compare/search_tests.py

echo ""
echo "完了しました。results/ を確認してください。"
echo "Kibana が必要な場合: docker compose --profile kibana up -d kibana  (http://localhost:5602)"
