# Image Search PoC — Elastic Cloud Serverless + Jina v5 Omni

Elastic Cloud Serverless と Jina の **`jina-embeddings-v5-omni-small`** (通称 Jina v5 Omni、small バリアント) を使ったマルチモーダル画像検索 PoC。Kibana の **Agent Builder チャット** から日本語・英語で画像を探せます。フロントエンドコードはゼロ行。

> 📝 **このリポジトリの解説ブログ**: [SIOS Tech ブログ — Elastic カテゴリ](https://elastic.sios.jp/category/blog/) で日本語のシリーズ記事として公開しています。本 PoC の動機・実装・運用までの全体像はそちらをご参照ください。

---

## 📌 Elastic のバージョンについて

本 PoC は **Elastic Cloud Serverless** を前提にしており、Kibana 上のバージョン表示は **9.5** です。

ただし、Elastic Stack の正式 GA 版 (自己ホスト / Elastic Cloud Hosted) は **9.4** が最新です (本記事執筆時点)。Serverless は GA 版より **先行リリース** されるしくみになっており、**Technical Preview 段階の機能** も含まれています。そのため Kibana に表示されるバージョン番号も GA 版より先に進んでいます。

本 PoC で使う主要機能のうち、特に次の 2 つは **Serverless でのみ利用可能** な Technical Preview 機能です:

- **Agent Builder** (`Agents` メニュー)
- **MCP connector** (`Tools library → Manage MCP`)

Self-managed の 9.4 や Elastic Cloud Hosted 9.4 では、これらは利用できないか、API 経由のみになります。本 PoC をそのまま再現する場合は **Elastic Cloud Serverless** をご利用ください。

---

## できること

3 つの検索モードを Agent Builder のチャットで使えます:

| 入力例 | 何が起きるか |
| --- | --- |
| 「青い椅子の写真」 | 自然言語で意味的に近い画像 上位 3 件を返す |
| 「IMG_8133.jpeg に似た画像」 | 既存ファイルから視覚的に似た画像 上位 3 件 (自分は除外) |
| 「'RIDE' と書かれた画像を探して」 | 画像内の文字を含む画像 上位 3 件 |

---

## アーキテクチャ

```
  ローカル開発機 (Mac)                 Elastic Cloud Serverless (Tokyo)
  ┌──────────────────────┐            ┌──────────────────────────────┐
  │ Python スクリプト    │   HTTPS    │ Elasticsearch (alias)        │
  │  setup / ingest / cli├───────────►│   dense_vector(1024)/cosine  │
  ├──────────────────────┤            │                              │
  │ MCP server           │            │ EIS                          │
  │  (FastMCP, :8080)    │            │   .jina-embeddings-v5-omni-  │
  │                      │            │   small (text + image)       │
  │                      │            │                              │
  │ ngrok agent          │◄───ngrok───┤ Agent Builder                │
  │                      │   tunnel   │   + MCP connector            │
  └──────────────────────┘            │   + Kibana chat UI           │
        │                             └──────────────────────────────┘
        ▼
  ┌──────────────────────┐
  │ AWS S3 (Tokyo)       │
  │  private bucket      │
  │  SSE-S3 / versioning │
  └──────────────────────┘
```

ポイント:

- 画像は **S3 のプライベートバケット** に保存。アクセスは **pre-signed URL (10 分有効)** 経由のみ
- 埋め込みは **`jina-embeddings-v5-omni-small`** (Jina v5 Omni シリーズの small バリアント、multimodal)。テキストと画像が同じ 1024 次元のベクトル空間に乗る
- ingest は Python 側で `_inference` を呼んでベクトル化 → index
- search は `_search` の中で `query_vector_builder` が自動的に `_inference` を呼ぶ (1 リクエスト完結)
- Agent Builder のツールは **MCP server** として公開。ngrok 経由で接続

---

## 必要なもの

- macOS (Apple Silicon でも Intel でも OK)
- Python 3.11 以上
- AWS アカウント (専用 IAM ユーザーを 1 つ用意)
- Elastic Cloud Serverless アカウント (Tokyo リージョン推奨)
- ngrok アカウント (無料プラン OK)
- 画像ファイル 10〜20 枚 (jpg / jpeg / png)

---

## セットアップ手順 (順番に)

> 💡 各 Phase の詳しい解説 (用語・図解・トラブル予防) は冒頭で紹介した [SIOS Tech ブログ](https://elastic.sios.jp/category/blog/) のシリーズ記事を参照してください。ここでは「動かすコマンド」と「最低限の前提」だけ載せます。

### Phase 0 — 環境準備

```bash
cd /path/to/test-jina-image
bash setup/check_prerequisites.sh
```

最初は `.env` が空なので失敗します。表示される指示に従って **`.env`** を埋めてから再実行:

```dotenv
# Elastic Cloud Serverless のエンドポイント (Kibana の URL の .kb. を .es. に変える)
ELASTIC_URL=https://image-search-poc-xxxxxx.es.ap-northeast-1.aws.elastic.cloud
# Kibana > Stack Management > API keys で作成した Encoded 値
ELASTIC_API_KEY=...

# AWS IAM ユーザーのキー (root を使わない)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# 東京リージョンの コードだけ (UI ラベル「Asia Pacific (Tokyo) ap-northeast-1」は NG)
AWS_REGION=ap-northeast-1

# 全 AWS で一意のバケット名
S3_BUCKET_NAME=image-search-poc-yourname-20260524

# 推奨デフォルト
S3_UPLOAD_PREFIX=poc-uploads
INDEX_NAME=image-search-poc
```

埋めたらもう一度実行 → 全項目 ✅ で完了。

### Phase 1 — S3 バケットを作成

```bash
./venv/bin/python setup/create_s3_bucket.py
```

設定される項目:
- Block all public access (4/4)
- SSE-S3 (AES-256)
- Versioning enabled
- ⚠ バケットポリシーは **作らない** (IAM identity 権限だけで運用)

### Phase 2 — Elasticsearch インデックスと alias を作成

```bash
./venv/bin/python setup/create_elastic_index.py
```

作成されるもの:
- 実体インデックス `image-search-poc-v1` (dense_vector 1024dim / cosine / int8_hnsw)
- alias `image-search-poc` → `-v1`

### Phase 3 — 画像を ingest

```bash
./venv/bin/python ingest/upload_and_index.py /path/to/poc-images
```

各画像について次の処理:

1. S3 にアップロード
2. ローカルファイルを **base64 + data URI** にエンコード (MIME は拡張子から自動判定: jpg/jpeg → `image/jpeg`、png → `image/png`)
3. **公式 content-block 形式** で `_inference` を呼び、1024 次元ベクトルを得る
4. `image_embedding` フィールドに格納して alias に index

#### 画像を削除したいとき

```bash
./venv/bin/python ingest/delete_images.py IMG_8687.jpg IMG_8866.jpeg
```

S3 と Elastic の両方から該当ドキュメントを削除します。冪等で、既に存在しないファイルを指定してもエラーになりません。

### Phase 4 — CLI から検索を確認

```bash
./venv/bin/python tools/search_tools.py text "青い椅子"
./venv/bin/python tools/search_tools.py filename "IMG_8133.jpeg"
./venv/bin/python tools/search_tools.py text_in_image "RIDE"
```

意味的に近い画像が 3 件、**pre-signed URL (10 分有効)** 付きで返ってきます。ブラウザで URL を開くと画像が表示されます。

> ⚠️ `_score` は kNN のランキング用スコアであって、AI の正解確率ではありません。`(1 + cos(θ)) / 2` を 100 倍した値で、相対的なランキング指標として使うのが正しい読み方です (詳細は「設計メモ」セクション参照)。

### Phase 5 — MCP server をローカルで立てる

Agent Builder からローカルの検索ロジックを呼べるように、**MCP server** を立てて **ngrok** でインターネット側に公開します。**2 ターミナル運用** を推奨します。

#### ターミナル A — ngrok を起動 (セッションごとに 1 回)

```bash
NGROK_AUTH="myuser:mypassword2026" bash agent/start_ngrok.sh
```

引数:
- `NGROK_AUTH="user:pass"` ... ngrok の Basic 認証情報。**固定値にしておくと Kibana 側のヘッダーを毎回触らなくて済む**
- パスワードは **8 文字以上** (ngrok の制約)
- 省略するとスクリプトがランダムな 16 文字パスワードを生成

起動後の出力:

```
Forwarding   https://abc123-xyz.ngrok-free.app -> http://localhost:8080
```

→ 表示された `https://abc123-xyz.ngrok-free.app` をメモ。Phase 6 で使います。

#### ターミナル B — MCP server を起動 (コード変更ごとに再実行)

```bash
bash agent/start_mcp.sh
```

`http://127.0.0.1:8080/mcp` で MCP server が待ち受け、ngrok 経由で外部から到達できます。コードを編集したらこのターミナルだけ Ctrl+C → 再実行。ngrok URL は変わりません。

### Phase 6 — Agent Builder で MCP コネクタを登録

#### 6-1. エージェントを作る

1. Kibana 左メニュー → **Agents** → **New Agent**
2. **Agent ID**: `image-search-agent`
3. **Custom Instructions** に [`agent/system_prompt.md`](./agent/system_prompt.md) の `===== COPY BELOW THIS LINE =====` 〜 `===== COPY ABOVE THIS LINE =====` の中身を貼る
4. **Elastic capabilities**: OFF (ビルトインツールは使わない)
5. **Visibility**: Private
6. Save

#### 6-2. MCP コネクタを登録

1. Kibana → **Tools library** → **Manage MCP** → **Add a new MCP server**
2. 次の値を入れる:

| 項目 | 値 |
| --- | --- |
| Connector name | `Image Search PoC` |
| Connector ID | `image-search-poc` |
| Server URL | `https://<your-ngrok>.ngrok-free.app/mcp` ← `/mcp` の suffix を忘れずに |

3. 「Additional settings」を展開して 2 つの HTTP ヘッダーを追加:

| Key | Value |
| --- | --- |
| `Authorization` | `Basic <base64 of user:pass>` (例: `Basic bXl1c2VyOm15cGFzc3dvcmQyMDI2`) |
| `ngrok-skip-browser-warning` | `true` |

Authorization の base64 は `printf 'myuser:mypassword2026' | base64` で計算。`echo` は末尾改行を含むので使わないこと。

#### 6-3. ツールを有効化

1. Save 後、ドロップダウンで `Image Search PoC` を選ぶ → 3 つのツールが表示される
2. 全部チェック → Namespace に `image_search` を入れて → **Import tools**
3. Agents → image-search-agent → **Tools** タブで `image_search.search_images_by_*` を 3 つ有効化
4. (推奨) デフォルトのビルトインツール 6 つは無効化
5. Save

#### 6-4. チャットで動作確認

エージェント画面右上の「Save and chat」を押して、次のクエリを入れる:

```
青い椅子の写真を見せて
```

3 件の結果カードに「画像を新しいタブで開く →」リンクが付いて返ってきます。

---

## 試してみるクエリ

### 1. 自然言語

```
青い椅子の写真を見せて
```

Agent は `search_images_by_text` を `query="青い椅子"` で呼ぶ。

### 2. 既存画像と類似のもの

```
IMG_8133.jpeg に似た画像を見せて
```

Agent は `search_images_by_filename` を `filename="IMG_8133.jpeg"` で呼ぶ。

### 3. 画像内文字

```
'RIDE' と書かれている画像を探して
```

Agent は `search_images_by_visible_text` を `visible_text="RIDE"` で呼ぶ。

---

## 起動と停止

2 ターミナル運用での起動・停止フローのまとめです。

- **セッション開始時**: ターミナル A で `start_ngrok.sh` → URL メモ → ターミナル B で `start_mcp.sh` → Kibana のコネクタの Server URL を更新 (ngrok free 版は起動ごとに URL が変わるため)
- **コード編集時**: ターミナル B だけ Ctrl+C → `start_mcp.sh` 再実行 (ngrok URL は変わらないので Kibana 側は触らない)
- **セッション終了時**: ターミナル B → ターミナル A の順に Ctrl+C
- **一時離席**: 両ターミナルを起動したままにしておけば URL は維持される

> 💡 ngrok の有料プランに切り替えれば固定 URL が使えるため、Server URL の付け替え自体が不要になります。チーム共有や本番運用に近い構成では Cloudflare Tunnel + Access への移行も選択肢です。

---

## トラブルシューティング

### A. `AWS_REGION` のフォーマット間違い

**症状:** `botocore.exceptions.InvalidRegionError: Provided region_name 'Asia Pacific (Tokyo) ap-northeast-1' doesn't match a supported format.`

**直し方:** `.env` の `AWS_REGION` をリージョンコードだけにする → `ap-northeast-1`

### B. `ELASTIC_URL` がどこにあるかわからない

Cloud Console には「Endpoint」と書かれた欄が見つかりにくい。

**直し方:** Kibana の URL の `.kb.` を `.es.` に書き換える。これがあなたの `ELASTIC_URL`。

### C. `ELASTIC_API_KEY` と Endpoint の取り違え

Cloud Console の Getting Started に出てくる「endpoint と暗号化された値」のうち、endpoint の右隣にあるマスク欄は **API キーではなくサンプル**。

**直し方:** Kibana > Stack Management > API keys > **Create API key** で作って **Encoded** の値をコピーする。

### D. S3 バケットを作れない (権限不足)

```
❌ アクセス拒否: IAM ユーザーに `s3:CreateBucket` 権限がない可能性があります。
```

**直し方:** AWS コンソールでバケットを手動で作る (リージョン: 東京、Block all public access ON)。スクリプトを再実行すると、存在確認 → セキュリティ設定だけ適用してくれる。

### E. S3 バケットポリシーを設定したら検索が壊れた

pre-signed URL が `Access Denied`、IAM identity 権限はあるはずなのに動かない。

**直し方:** バケットポリシーを **削除** する。この PoC では IAM identity 権限だけで運用する設計。バケットポリシーは触らない。

### F. インデックス名が `_` で始まると 400 エラー

Serverless では先頭 `_` のインデックス名はシステム予約。

**直し方:** インデックス名はハイフン区切り (例: `image-search-poc-v1`)。

### G. pre-signed URL が「Access Denied」で開けない

**原因 1:** CLI 出力で URL が **省略** されていた (`...` で truncate)。コピー時に signature が途中で切れて認証失敗。
→ `search_tools.py` は現在切らずに表示する。URL を全文使う。

**原因 2:** IAM ユーザーに `s3:GetObject` が無い。
→ IAM ポリシーに `s3:GetObject` を追加。

### H. 画像 embed の API レスポンスのキー名が想定外

```
❌ 失敗: 埋め込みが見つかりません。レスポンスのキー: ['embeddings']
```

Elastic 9.5 の `jina-embeddings-v5-omni-small` のレスポンスは `embeddings` (複数形)。古いコード例は `embedding` や `text_embedding` を期待していた。

**直し方:** すでに `ingest/upload_and_index.py` で対応済み — 複数のキー名を順に試すフォールバックを実装。

### I. ⭐ 一番厄介な罠 — 画像 URL を文字列として送ると text embedding になる

ingest は成功するが、検索結果が滅茶苦茶。"sea" で検索すると 椅子+PC の写真が出る、スコアが全画像 58% に張り付く、違う画像同士のコサイン類似度が 0.94 になる。

**原因:** `_inference` の入力を「pre-signed URL の文字列」や「base64 だけの文字列」にすると、Elastic は それを **テキスト** として扱う。`jina-embeddings-v5-omni-small` の画像エンコーダ経路に入らない。

**直し方:** ローカルファイルを base64 にして、**公式 content-block 形式** で送る:

```json
POST _inference/.jina-embeddings-v5-omni-small
{
  "input": [
    {
      "content": {
        "type": "image",
        "format": "base64",
        "value": "data:image/jpeg;base64,<RAW_BASE64>"
      }
    }
  ]
}
```

3 つのポイント:
- `content` は **配列ではなく単一オブジェクト**
- `value` には **`data:image/jpeg;base64,`** の prefix を付ける (PNG なら `image/png`)
- 入力は **base64 された画像データ**。URL は NG (text embedding になる)

### J. semantic_text フィールドに画像を入れたら大幅劣化した

開発の途中で `semantic_text` フィールドを試したら、全画像がコサイン 0.94 でクラスタリングして検索が壊れた。

**原因:** `semantic_text` は **テキスト** 用に設計されている。base64 文字列をチャンク分割してテキストとして埋め込んでしまう (どの JPEG も同じ JFIF ヘッダで始まるため、最初のチャンクが全部似てしまう)。

**直し方:** 画像には `dense_vector` + content-block 形式の `_inference` を使う (= Phase 3 のやり方)。

### K. Agent Builder の chat で画像 (inline) が壊れたアイコンで表示される

チャットの返信に画像カードが出るが、アイコンが「broken image」になる。DevTools の Network タブで S3 リクエストが `(blocked:csp)` となっている。

**原因:** Kibana の Content Security Policy が `img-src` に外部ドメイン (s3.amazonaws.com) を許可していない。**Elastic Cloud Serverless ではこの設定はカスタマイズ不可**。

**対処:** システムプロンプトを「インライン画像 `![](url)`」から「クリッカブルリンク `[label](url)`」に変更する。`agent/system_prompt.md` は既にその形式になっている。

### L. ngrok 利用上の落とし穴

- **`ERR_NGROK_4018`** → サインアップ + `ngrok config add-authtoken <TOKEN>` を一度実行する必要がある
- **`Invalid basic auth credential. Password must be between 8 and 128 characters.`** → basic auth のパスワードは 8 文字以上にする
- **free 版だと tunnel を立てるたびに URL が変わる** → `start_ngrok.sh` で ngrok を立てっぱなしにする (2 ターミナル運用)
- **"browser warning page" が出る** → connector で `ngrok-skip-browser-warning: true` ヘッダを追加で送る

### M. ngrok を再起動したら「Failed to load tools」が出る

前日まで動いていたのに、ngrok を一度落として再起動した直後、Kibana の Bulk import で「Failed to load tools from the selected MCP server」が表示される。

**原因:** `start_ngrok.sh` は環境変数 `NGROK_AUTH` が無いと **毎回ランダムなパスワード** を生成する。前日に登録した Kibana の Authorization ヘッダーは **昨日のパスワード** の base64 のままなので、ngrok 側で 401 → Elastic は HTML エラーページを受け取り MCP プロトコルとして解析失敗。

**直し方 (推奨):** ngrok 起動時に毎回同じ `NGROK_AUTH` を渡す:

```bash
NGROK_AUTH="myuser:mypassword2026" bash agent/start_ngrok.sh
```

**診断のコツ:** 「Failed to load tools」が出たら curl で直接叩いて切り分け:

```bash
curl -i -u "$(cat /tmp/mcp_demo_auth.txt)" \
  -H "ngrok-skip-browser-warning: true" \
  https://<your-ngrok>.ngrok-free.app/mcp
```

- `401 Unauthorized` → 認証情報が違う
- `404 Not Found` → URL 末尾が `/mcp` になっていない
- HTML が返る → `ngrok-skip-browser-warning` ヘッダー漏れ
- 接続拒否 → MCP server が動いていない

### N. Agent Builder の MCP connector でツールが読み込めない

「Failed to load tools from the selected MCP server」エラーの一般的な原因 (M 以外):

1. **transport 不一致:** Agent Builder は Streamable HTTP を使う (`POST /mcp` で JSON-RPC)。`mcp_server.py` で `transport="streamable-http"` を指定すること
2. **エンドポイント path 不一致:** Server URL は `https://<ngrok>/mcp` で終わるようにする
3. **auth header の入れ方ミス:** `Key=Authorization`, `Value=Basic <base64>` の 1 行にする

ngrok の inspector (`http://127.0.0.1:4040`) を見れば、Elastic が実際に送ってくるリクエスト (URL, headers, body) が分かるので診断に有用。

### O. Agent Builder の MCP connector を削除したい

9.5 TECHNICAL PREVIEW の時点では、Manage MCP のドロップダウンに delete オプションが無い。**Stack Management → Connectors** から探すか、Kibana の Connectors API を Dev Tools で叩いて削除する。

---

## 設計メモ

- **alias の意味:** アプリ側は alias 名しか知らない。実体は `-v1`, `-v2`... と進化させ、alias を付け替えれば downstream は無修正
- **ingest は Python 側で `_inference`:** ingest 時は Python が `_inference` を叩いて vector を index に入れる
- **search は `query_vector_builder`:** query 時は **逆に Elastic が `_inference` を呼ぶ**。`_search` 1 リクエストで完結 (`query_vector_builder.embedding` または `query_vector_builder.lookup`)
- **pre-signed URL は永続化しない:** 10 分有効。検索のたびに新しく生成する。S3 は private のまま
- **MIME タイプは拡張子から自動判定:** `.jpg`/`.jpeg` → `image/jpeg`、`.png` → `image/png` (`ingest/upload_and_index.py`)
- **バケットポリシーは作らない:** IAM identity 権限 + SSE-S3 + Block Public Access の 3 つだけ
- **MCP server は `127.0.0.1` で bind:** LAN からの直接アクセスを防ぐ。外部からは ngrok 経由でのみ到達可
- **スコアは確率ではない:** `_score` は kNN のランキング指標。`(1 + cos(θ)) / 2` を 100 倍した値
- **alias rollback:** `setup/revert_alias_to_v1.py` を残してある

---

## ファイル構成

```
test-jina-image/
├── README.md                        # このファイル
├── .env                             # 認証情報 (Git にコミット禁止)
├── .env.example                     # テンプレート
├── .gitignore                       # .env, venv/, __pycache__/, ローカル限定ドキュメントを除外
├── venv/                            # Python 仮想環境
├── setup/
│   ├── check_prerequisites.sh       # Phase 0 — 環境チェック + venv 作成
│   ├── create_s3_bucket.py          # Phase 1 — S3 バケット作成
│   ├── create_elastic_index.py      # Phase 2 — インデックス + alias 作成
│   └── revert_alias_to_v1.py        # 緊急 rollback 用
├── ingest/
│   ├── upload_and_index.py          # Phase 3 — 画像アップロード + ベクトル化 + index
│   └── delete_images.py             # 画像削除 (S3 と Elastic 両方から)
├── tools/
│   ├── search_tools.py              # Phase 4 — CLI 検索 (3 つの検索関数本体)
│   ├── diagnose_embeddings.py       # 開発中に使った診断ツール
│   ├── test_image_formats.py        # 開発中に使った診断ツール
│   ├── test_endpoint_options.py     # 開発中に使った診断ツール
│   ├── test_official_format.py     # 開発中に使った診断ツール
│   └── test_semantic_text_image.py  # 開発中に使った診断ツール
├── agent/
│   ├── mcp_server.py                # Phase 5 — MCP server (FastMCP)
│   ├── system_prompt.md             # Agent Builder の Instructions に貼る
│   ├── esql_tools.md                # Search Template 方式の代替案 (検討時の記録)
│   ├── start_ngrok.sh               # ターミナル A 用
│   ├── start_mcp.sh                 # ターミナル B 用
│   └── start_demo.sh                # 1 ターミナルで両方起動 (非推奨; 開発初期の名残)
└── screenshots/                     # ブログ用のスクリーンショット
    ├── Agents/
    └── tools/
```

---

## 関連リソース

### このリポジトリの解説ブログ

**[SIOS Tech ブログ — Elastic カテゴリ](https://elastic.sios.jp/category/blog/)** — 本 PoC の動機、実装、ハマったところ、運用までを日本語のシリーズ記事として連載しています。Elastic 関連の検証記事も合わせて掲載。

### リポジトリ内ドキュメント

- [agent/system_prompt.md](./agent/system_prompt.md) — Agent Builder にコピペする system prompt
- [agent/esql_tools.md](./agent/esql_tools.md) — Search Template 方式の代替案 (検討記録)

### 公式参考リンク

- [Elastic Search Labs — jina-embeddings-v5-omni for text, images, video, audio](https://www.elastic.co/search-labs/blog/jina-embeddings-v5-omni-all-media-one-index)
- [Elastic Docs — Inference embedding API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-inference-embedding)
- [Elastic Docs — Elastic Inference Service](https://www.elastic.co/docs/explore-analyze/elastic-inference/eis)
- [Elastic Docs — Agent Builder Tools](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/tools)
- [Jina AI — v5 Omni 発表](https://jina.ai/news/jina-embeddings-v5-omni-multimodal-embeddings-for-text-image-audio-and-video/)
- [Model Context Protocol (MCP) 仕様](https://modelcontextprotocol.io/)
- [FastMCP (Python MCP server framework)](https://gofastmcp.com)
- [ngrok ドキュメント](https://ngrok.com/docs)
