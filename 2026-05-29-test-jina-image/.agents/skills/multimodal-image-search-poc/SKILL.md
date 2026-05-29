---
name: multimodal-image-search-poc
description: >
  Elastic Cloud Serverless 9.5+ と Jina v5 Omni を使ったマルチモーダル画像検索 PoC を
  構築するためのガイド。dense_vector + content-block 形式の _inference、query_vector_builder、
  Agent Builder の MCP カスタムツール統合、ngrok 経由のローカル MCP server 公開、
  Kibana CSP の制限など、実装でハマるポイントすべてを含む。
  ユーザーが「画像検索」「マルチモーダル検索」「Agent Builder にカスタムツールを足したい」
  「Jina v5 Omni を Elastic で使いたい」と言ったときに発動する。
compatibility: Elastic Cloud Serverless 9.5+ / Jina v5 Omni
metadata:
  author: 自家製 (Image Search PoC プロジェクトから抽出)
  version: 1.0.0
---

# Multimodal Image Search PoC — Skill Guide

あなたは Elastic + 多モーダル AI モデルを使った画像検索システムの構築をガイドするアシスタントです。
本スキルは、過去に同じ PoC を実際に作って学んだ知識をまとめたもので、**繰り返しハマる罠** と
**正解の実装パターン** を持っています。

---

## このスキルが扱う典型シナリオ

ユーザーから以下のような要望が出たら、このスキルを使ってください。

- 「Elastic で画像検索したい」
- 「マルチモーダルモデルを Elastic で使いたい」
- 「Jina v5 Omni を Elastic Cloud Serverless で動かしたい」
- 「Kibana の Agent Builder に独自のツールを追加したい」
- 「テキストで画像を検索する PoC を作りたい」
- 「kNN + dense_vector で画像を検索したい」
- 「写真をアップロードして似た画像を検索する仕組みを作りたい」

---

## 全体アーキテクチャの推奨パターン

```
Mac (or PoC マシン)               Elastic Cloud Serverless (Tokyo)
┌─────────────────────┐           ┌──────────────────────────────┐
│ Python スクリプト   │   HTTPS   │ Elasticsearch                │
│  - ingest           ├──────────►│   dense_vector(1024)          │
│  - search           │           │   int8_hnsw / cosine          │
│  - MCP server       ◄──────────►│ EIS (Jina v5 Omni)            │
└────────┬───────────┘   ngrok    │ Agent Builder (MCP connector) │
         ▼                        └──────────────────────────────┘
┌─────────────────────┐
│ AWS S3 (private)    │
│ pre-signed URL only │
└─────────────────────┘
```

---

## 推奨される技術選択 (Decision Tree)

### Step 1: モデル選択

**画像 + テキストの両方を検索するなら → `.jina-embeddings-v5-omni-small`**

理由:
- GA ステータス (`jina-clip-v2` は preview)
- 4 モダリティ対応 (text/image/audio/video) で将来拡張可
- 1024 次元・cosine 類似度
- Elastic Cloud Serverless にプリインストール済み

```
GET _inference/_all
```
で利用可能なエンドポイントを確認。

### Step 2: ベクトルの保存方法

**画像には `dense_vector` を使う。`semantic_text` は NG。**

| フィールド型 | 用途 |
| --- | --- |
| `dense_vector` ⭐ | 画像、明示的にベクトルを保存・kNN したいとき |
| `semantic_text` | テキストのみ。base64 を入れるとチャンク分割されて壊れる |

理由 (重要): `semantic_text` は内部でテキストとして扱うため、base64 文字列を渡すと
チャンク分割して個別に embedding し、JPEG ヘッダの共通性で全画像がクラスタリングしてしまう。

推奨マッピング:

```json
{
  "image_embedding": {
    "type": "dense_vector",
    "dims": 1024,
    "index": true,
    "similarity": "cosine",
    "index_options": { "type": "int8_hnsw" }
  }
}
```

`int8_hnsw` でメモリを約 1/4 に削減できる (精度ほぼ同じ)。

### Step 3: 画像の _inference 呼び出し方

**必ず content block 形式で送る。URL や生 base64 文字列は NG。**

正しい形式:

```json
POST _inference/embedding/.jina-embeddings-v5-omni-small
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

3 つの守るべきポイント:
- `content` は **単一オブジェクト** (配列ではない)
- `value` は **`data:image/jpeg;base64,`** prefix 付き
- 入力は **base64 された画像データ** (S3 の pre-signed URL は NG)

理由: 文字列を直接渡すと Elastic はテキストとして embedding する。「URL の文字列」を
ベクトル化することになり、画像内容は反映されない。

Python 例:

```python
import base64

b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
data_uri = f"data:image/jpeg;base64,{b64}"

response = es.inference.inference(
    inference_id=".jina-embeddings-v5-omni-small",
    input=[{
        "content": {
            "type": "image",
            "format": "base64",
            "value": data_uri,
        }
    }],
)

# レスポンスのキーは "embeddings" (複数形)
embedding = response["embeddings"][0]["embedding"]
```

### Step 4: 検索時の embedding 生成

**`query_vector_builder` を使う。クライアント側で _inference を別途呼ばない。**

検索クエリの中で Elastic 自身に embedding させる:

```json
{
  "knn": {
    "field": "image_embedding",
    "k": 3,
    "num_candidates": 50,
    "query_vector_builder": {
      "embedding": {
        "inference_id": ".jina-embeddings-v5-omni-small",
        "input": { "type": "text", "value": "赤い椅子" }
      }
    }
  }
}
```

メリット: 1 リクエストで text→vector→kNN が完結。クライアントコードがシンプル。

「既存 doc の embedding を使った類似検索」なら `lookup` バリエーション:

```json
{
  "knn": {
    "field": "image_embedding",
    "k": 4,
    "query_vector_builder": {
      "lookup": {
        "index": "image-search-poc",
        "id": "poc-uploads/IMG_8133.jpeg",
        "path": "image_embedding"
      }
    }
  }
}
```

### Step 5: インデックス設計に alias を使う

**実体名は `<name>-v1` のように versioned、alias 名はバージョン無し。**

```http
PUT image-search-poc-v1
{ "mappings": { ... } }

POST /_aliases
{
  "actions": [
    { "add": { "index": "image-search-poc-v1", "alias": "image-search-poc" } }
  ]
}
```

将来マッピング変更が必要になったら `-v2` を作って alias を atomically 切り替えれば済む。
アプリは alias 名でしか操作しないので無修正。

### Step 6: Agent Builder のツール統合方法

**Custom Tool の Type は 4 つから選択する。**

| Type | できること | このユースケースで使えるか |
| --- | --- | --- |
| ES\|QL | 固定の ES\|QL クエリ + パラメータ | ❌ text→vector 変換ができない |
| Index search | LLM が ES\|QL を自然言語から生成 | ❌ 同上 |
| Workflow | 複数ステップの workflow を呼ぶ | △ オーバーキル |
| **MCP** ⭐ | 外部の MCP server を呼ぶ (任意言語) | ✅ 推奨 |

`query_vector_builder` を含む DSL クエリを使う場合、ES|QL では表現できないため
**MCP server (Python の FastMCP) を立てる** のが現実的。

### Step 7: MCP server の立て方

```python
from fastmcp import FastMCP

mcp = FastMCP("image-search-poc")

@mcp.tool()
def search_images_by_text(query: str) -> list:
    """画像を自然言語で検索する"""
    return search_logic(query)

mcp.run(
    transport="streamable-http",   # SSE ではなく streamable-http が Agent Builder の正解
    host="127.0.0.1",              # 0.0.0.0 は NG (LAN 露出)
    port=8080,
)
```

エンドポイント path は `/mcp` (デフォルト)。

### Step 8: Agent Builder からの公開方法

**Elastic Cloud Serverless は内部ネットワーク経由でローカルに到達できない。インターネット公開が必要。**

| 方法 | URL の安定性 | 認証 | コスト | 推奨度 |
| --- | --- | --- | --- | --- |
| ngrok 無料 | ❌ セッションごと変わる | Basic auth | $0 | PoC 用 |
| ngrok 有料 | ✅ 静的 | Basic auth | $8/月 | 個人開発 |
| Cloudflare Tunnel + Access | ✅ 静的 | Google/GitHub | $0 | **チーム共有** ⭐ |
| AWS Lambda + API Gateway | ✅ 静的 | API key | ほぼ $0 | 本番運用 |

### Step 9: Agent Builder MCP connector の設定

必須項目:

- **Server URL**: `https://<tunnel>/mcp` (末尾 `/mcp` を忘れずに)
- **Header 1**: `Authorization: Basic <base64(user:pass)>` ← base64 は事前計算する
- **Header 2**: `ngrok-skip-browser-warning: true` ← ngrok 経由の場合必須

```bash
# Authorization 値の計算
printf 'samadmin:imagepoc2026' | base64
# → c2FtYWRtaW46aW1hZ2Vwb2MyMDI2
```

### Step 10: 画像表示の制約

**Kibana Agent Builder のチャット UI は CSP で外部画像をブロックする。インライン埋め込み (`![]()`) は NG。**

回避策: system prompt で **clickable link (`[label](url)`)** を出すよう指示する。
Elastic Cloud Serverless では CSP のカスタマイズはサポート対象外。

S3 pre-signed URL を生成するとき、ブラウザに「画像」として認識させるため
`ResponseContentType` を指定する:

```python
s3.generate_presigned_url(
    "get_object",
    Params={
        "Bucket": bucket,
        "Key": key,
        "ResponseContentType": "image/jpeg",   # ← inline 表示用
    },
    ExpiresIn=600,   # 10 分 (短いほど安全)
)
```

---

## やってはいけないこと (Anti-patterns)

1. ❌ **`_inference` に S3 の URL を文字列で渡す** → テキスト扱いになり embedding が壊れる
2. ❌ **画像を `semantic_text` フィールドに入れる** → チャンク分割でクラスタリング
3. ❌ **`AWS_REGION` に `"Asia Pacific (Tokyo) ap-northeast-1"` と書く** → boto3 が受け付けない (`ap-northeast-1` のみ)
4. ❌ **`ELASTIC_URL` に Kibana の `.kb.` URL を使う** → 認証エラー (`.es.` に変換する)
5. ❌ **MCP server を `host="0.0.0.0"` で起動** → LAN から ngrok 認証バイパス可
6. ❌ **インデックス名を `_` で始める** → Serverless では予約名で 400 エラー
7. ❌ **S3 バケットポリシーを付ける** → IAM identity 権限と衝突して 403 になりがち
8. ❌ **エージェントの応答に `![](url)` で画像を埋め込む** → Kibana の CSP でブロック
9. ❌ **`Authorization: Basic <base64(user:pass)>` をリテラル文字列で connector に登録** → 実際の base64 値を計算して入れる
10. ❌ **ngrok の basic auth パスワードを 8 文字未満にする** → ngrok が拒否
11. ❌ **`ngrok-skip-browser-warning` ヘッダーを付け忘れる** → ngrok が HTML 警告ページを返してしまう
12. ❌ **`echo 'user:pass' | base64`** → 末尾改行が入って間違った値になる (`printf` を使う)

---

## 必須トラブルシューティング 5 件

| 症状 | 原因 | 対処 |
| --- | --- | --- |
| `InvalidRegionError: 'Asia Pacific (Tokyo) ap-northeast-1'` | UI ラベルをコピーしている | `AWS_REGION=ap-northeast-1` だけにする |
| `ELASTIC_URL` が見つからない | Cloud Console に endpoint 欄が無い | Kibana URL の `.kb.` を `.es.` に変える |
| 異なる画像が cosine 0.94 (テキスト扱い) | content block を使っていない | base64 + content block 形式で送る |
| Agent Builder の「Failed to load tools」 | 多数の原因 (transport, auth, ngrok 警告) | ngrok inspector (127.0.0.1:4040) で実際のリクエスト確認 |
| チャットで画像が broken icon | Kibana CSP が外部画像ブロック | clickable link で代替 (`[label](url)`) |

---

## セキュリティチェックリスト

- [ ] `.env` の権限は `chmod 600`
- [ ] `/tmp/mcp_demo_auth.txt` も `chmod 600` + プロセス終了時に削除
- [ ] MCP server は `127.0.0.1` のみ bind
- [ ] pre-signed URL の TTL は短く (600 秒推奨)
- [ ] ngrok basic auth は 8 文字以上のパスワード
- [ ] AWS IAM は最小権限 (resource ARN でバケット限定)
- [ ] S3 バケットは Block Public Access (4/4 全 ON) + SSE-S3 + Versioning
- [ ] バケットポリシーは付けない (IAM identity 権限のみ)
- [ ] `NGROK_AUTH="..."` は shell 履歴に残さない (`HIST_IGNORE_SPACE`)
- [ ] チーム共有なら ngrok ではなく Cloudflare Tunnel + Access へ

---

## 確認用コマンド

開発・運用中に役立つ Dev Tools / ターミナルのコマンド集:

```http
# 利用可能な inference エンドポイント一覧
GET _inference/_all

# クラスタ情報 (バージョン確認)
GET /

# alias の確認
GET _alias/<alias-name>

# alias の atomic 切り替え
POST /_aliases
{
  "actions": [
    { "remove": { "index": "image-search-poc-v1", "alias": "image-search-poc" } },
    { "add":    { "index": "image-search-poc-v2", "alias": "image-search-poc" } }
  ]
}

# インデックスのフィールド別ディスク使用量
POST <index>/_disk_usage?run_expensive_tasks=true

# 検索テンプレート登録
PUT _scripts/<template-id>
{ "script": { "lang": "mustache", "source": { ... } } }

# 接続テスト (curl)
curl -i -u 'user:pass' \
  -H 'ngrok-skip-browser-warning: true' \
  https://<ngrok>/mcp
# 期待される応答: HTTP/2 406 (auth 通過、MCP プロトコル待ち)
```

---

## 推奨ファイル構成

```
<project-root>/
├── .env                       # 認証情報 (chmod 600)
├── .env.example
├── .gitignore                 # .env, venv/ を除外
├── setup/
│   ├── check_prerequisites.sh
│   ├── create_s3_bucket.py
│   └── create_elastic_index.py
├── ingest/
│   └── upload_and_index.py    # content block 形式での ingest
├── tools/
│   └── search_tools.py        # query_vector_builder ベースの search
└── agent/
    ├── system_prompt.md       # clickable link 出力を指示
    ├── mcp_server.py          # FastMCP wrapper (127.0.0.1, streamable-http)
    ├── start_ngrok.sh         # ターミナル A
    └── start_mcp.sh           # ターミナル B
```

---

## ガイドライン (このスキルでユーザーを助けるとき)

- ユーザーが Elastic 初心者なら、まず用語 (embedding, kNN, alias) を確認する
- 画像を含むなら、必ず content block 形式の話をする (テキスト扱いの罠)
- Agent Builder 統合の話が出たら、MCP が必要だと言う前に、ES|QL で表現可能かを検討
- Serverless と self-managed では制約が違うので、必ず確認する (CSP カスタマイズ可否など)
- ハマったらまず ngrok inspector (`127.0.0.1:4040`) や Dev Tools の API レスポンスを確認
- セキュリティの話が出たら、`.env` 権限・MCP の host バインド・pre-signed URL TTL の 3 点を必ず確認

---

## 参考リンク

- [Elastic Search Labs — jina-embeddings-v5-omni for text, images, video, audio](https://www.elastic.co/search-labs/blog/jina-embeddings-v5-omni-all-media-one-index)
- [Elastic Docs — Inference embedding API](https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-inference-embedding)
- [Elastic Docs — Elastic Inference Service](https://www.elastic.co/docs/explore-analyze/elastic-inference/eis)
- [Elastic Docs — Agent Builder Tools](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/tools)
- [Model Context Protocol (MCP) 仕様](https://modelcontextprotocol.io/)
- [FastMCP](https://gofastmcp.com)
- [ngrok ドキュメント](https://ngrok.com/docs)
