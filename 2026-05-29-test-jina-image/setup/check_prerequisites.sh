#!/usr/bin/env bash
# Phase 0: PoC を始める前の環境チェックを行うスクリプト
# Image Search PoC for Elastic 9.4 + Jina v5 Omni

# プロジェクトのルートディレクトリへ移動する
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

# 端末で色を使うための定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# チェック結果を入れる配列を初期化する
PASS_LIST=()
FAIL_LIST=()

# 成功メッセージを表示して結果を記録する関数
ok() {
    printf "${GREEN}✅ %s${NC}\n" "$1"
    PASS_LIST+=("$1")
}

# 失敗メッセージを表示して結果を記録する関数
fail() {
    printf "${RED}❌ %s${NC}\n" "$1"
    FAIL_LIST+=("$1")
}

# 進行中のメッセージを表示する関数
info() {
    printf "${BLUE}▶ %s${NC}\n" "$1"
}

# 区切り線を表示する関数
hr() {
    printf "%s\n" "============================================================"
}

hr
printf "  Image Search PoC - 環境準備チェック (Phase 0)\n"
hr
printf "\n"

# Python 3.11 以上がインストールされているか確認する関数
check_python() {
    info "Python のバージョンを確認しています..."
    if ! command -v python3 >/dev/null 2>&1; then
        fail "Python3 が見つかりません。'brew install python@3.11' でインストールしてください。"
        return
    fi
    local ver
    ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    local major minor
    major=$(printf "%s" "$ver" | cut -d. -f1)
    minor=$(printf "%s" "$ver" | cut -d. -f2)
    if [ -z "$major" ] || [ -z "$minor" ]; then
        fail "Python バージョンの取得に失敗しました"
        return
    fi
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
        fail "Python 3.11 以上が必要です（現在: $ver）。'brew install python@3.11' を実行してください。"
        return
    fi
    ok "Python $ver が見つかりました"
}

# pip が使えるか確認する関数
check_pip() {
    info "pip を確認しています..."
    if ! python3 -m pip --version >/dev/null 2>&1; then
        fail "pip が見つかりません。'python3 -m ensurepip --upgrade' を実行してください。"
        return
    fi
    ok "pip が使えます"
}

# AWS CLI がインストールされているか確認する関数
check_aws_cli() {
    info "AWS CLI を確認しています..."
    if ! command -v aws >/dev/null 2>&1; then
        fail "AWS CLI が見つかりません。'brew install awscli' でインストールしてください。"
        return
    fi
    local v
    v=$(aws --version 2>&1 | head -1)
    ok "AWS CLI が見つかりました ($v)"
}

# Python 仮想環境（venv）を作成または再利用する関数
setup_venv() {
    info "Python 仮想環境を準備しています..."
    if [ -d "venv" ] && [ -x "venv/bin/python" ]; then
        ok "既存の venv をそのまま使います"
        return
    fi
    if python3 -m venv venv >/dev/null 2>&1; then
        ok "venv を ./venv に作成しました"
    else
        fail "venv の作成に失敗しました。Python の標準ライブラリ 'venv' が利用可能か確認してください。"
    fi
}

# 必要な Python パッケージを venv にインストールする関数
install_packages() {
    info "必要な Python パッケージをインストールしています（少し時間がかかります）..."
    if [ ! -x "venv/bin/pip" ]; then
        fail "venv/bin/pip が見つからないためインストールできません"
        return
    fi
    if ! ./venv/bin/pip install --quiet --upgrade pip >/dev/null 2>&1; then
        fail "pip の更新に失敗しました"
        return
    fi
    if ./venv/bin/pip install --quiet elasticsearch boto3 python-dotenv requests >/dev/null 2>&1; then
        ok "elasticsearch / boto3 / python-dotenv / requests をインストールしました"
    else
        fail "パッケージのインストールに失敗しました。ネットワーク接続を確認してください。"
    fi
}

# .env を .env.example からコピーする関数
create_env_file() {
    info ".env ファイルを確認しています..."
    if [ -f ".env" ]; then
        ok ".env はすでに存在します"
        return
    fi
    if [ ! -f ".env.example" ]; then
        fail ".env.example が見つかりません（プロジェクト構成に問題があります）"
        return
    fi
    cp .env.example .env
    ok ".env を .env.example からコピーしました（中身は後で編集します）"
}

# .gitignore がなければ作成する関数
create_gitignore() {
    info ".gitignore を確認しています..."
    if [ -f ".gitignore" ]; then
        ok ".gitignore はすでに存在します"
        return
    fi
    cat > .gitignore <<'EOF'
.env
venv/
__pycache__/
*.pyc
.DS_Store
EOF
    ok ".gitignore を作成しました"
}

# .env の中で必要な変数が埋まっているかチェックする関数
check_env_values() {
    info ".env の中身を確認しています..."
    if [ ! -f ".env" ]; then
        fail ".env が無いため確認できません"
        return
    fi

    # .env の値を取り出すヘルパー
    get_env_value() {
        local key="$1"
        # コメント行を除外、key=value を抽出、両端の空白とクォートを削除
        grep -E "^${key}=" .env 2>/dev/null \
            | head -n 1 \
            | cut -d= -f2- \
            | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
    }

    local required_keys=(
        "ELASTIC_URL"
        "ELASTIC_API_KEY"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "AWS_REGION"
        "S3_BUCKET_NAME"
        "S3_UPLOAD_PREFIX"
        "INDEX_NAME"
    )

    local missing=()
    for k in "${required_keys[@]}"; do
        local v
        v=$(get_env_value "$k")
        if [ -z "$v" ]; then
            missing+=("$k")
        fi
    done

    if [ ${#missing[@]} -eq 0 ]; then
        ok ".env のすべての変数が設定されています"
        return
    fi

    fail ".env に未設定の変数があります（${#missing[@]} 件）"
    printf "\n"
    printf "${YELLOW}未設定の変数：${NC}\n"
    for k in "${missing[@]}"; do
        printf "  - %s\n" "$k"
    done
    printf "\n"

    # ELASTIC_API_KEY が空ならガイドを表示する
    for k in "${missing[@]}"; do
        if [ "$k" = "ELASTIC_API_KEY" ]; then
            print_elastic_api_key_guide
            break
        fi
    done

    # 推奨値があるものはヒントを出す
    print_default_value_hints "${missing[@]}"
}

# Elastic API キーの作り方を日本語で案内する関数
print_elastic_api_key_guide() {
    printf "${YELLOW}--- Elastic API キーの作り方 ---${NC}\n"
    printf "  1) ブラウザで Elastic Cloud Serverless のプロジェクト (Kibana) を開く\n"
    printf "  2) 左メニューから [Stack Management] をクリック\n"
    printf "  3) [Security] セクションの [API keys] をクリック\n"
    printf "  4) [Create API key] ボタンを押す\n"
    printf "  5) Name に「image-search-poc」と入力（権限はデフォルトのまま）\n"
    printf "  6) [Create API key] を押す\n"
    printf "  7) 表示された [Encoded] の値をコピー\n"
    printf "  8) このプロジェクトの .env を開いて ELASTIC_API_KEY=<値> に貼り付け\n"
    printf "     ※ 「Encoded」の値（base64エンコード済み）を使ってください\n"
    printf "\n"
}

# 推奨値（東京リージョン、インデックス名など）のヒントを出す関数
print_default_value_hints() {
    local missing=("$@")
    local shown=0
    for k in "${missing[@]}"; do
        case "$k" in
            AWS_REGION)
                if [ $shown -eq 0 ]; then
                    printf "${YELLOW}--- .env に書く推奨値（コピペ用）---${NC}\n"
                    shown=1
                fi
                printf "  AWS_REGION=ap-northeast-1\n"
                ;;
            S3_UPLOAD_PREFIX)
                if [ $shown -eq 0 ]; then
                    printf "${YELLOW}--- .env に書く推奨値（コピペ用）---${NC}\n"
                    shown=1
                fi
                printf "  S3_UPLOAD_PREFIX=poc-uploads\n"
                ;;
            INDEX_NAME)
                if [ $shown -eq 0 ]; then
                    printf "${YELLOW}--- .env に書く推奨値（コピペ用）---${NC}\n"
                    shown=1
                fi
                printf "  INDEX_NAME=image-search-poc\n"
                ;;
            S3_BUCKET_NAME)
                if [ $shown -eq 0 ]; then
                    printf "${YELLOW}--- .env に書く推奨値（コピペ用）---${NC}\n"
                    shown=1
                fi
                printf "  S3_BUCKET_NAME=image-search-poc-<your-initials>-$(date +%Y%m%d)\n"
                ;;
        esac
    done
    [ $shown -eq 1 ] && printf "\n"
}

# メインの実行順序
check_python
check_pip
check_aws_cli
setup_venv
install_packages
create_env_file
create_gitignore
check_env_values

# 結果のまとめを表示する
printf "\n"
hr
printf "  チェック結果まとめ\n"
hr
printf "${GREEN}  成功: %d 件${NC}\n" "${#PASS_LIST[@]}"
printf "${RED}  要対応: %d 件${NC}\n" "${#FAIL_LIST[@]}"

if [ ${#FAIL_LIST[@]} -gt 0 ]; then
    printf "\n${YELLOW}要対応の項目：${NC}\n"
    for item in "${FAIL_LIST[@]}"; do
        printf "  ${RED}- %s${NC}\n" "$item"
    done
    printf "\n"
    printf "上記を解決してから、もう一度このスクリプトを実行してください。\n"
    printf "  実行コマンド: ${BLUE}bash setup/check_prerequisites.sh${NC}\n"
    exit 1
fi

printf "\n"
printf "${GREEN}🎉 すべてのチェックに合格しました！${NC}\n"
printf "次は Phase 1（S3 バケットの作成）に進めます。\n"
exit 0
