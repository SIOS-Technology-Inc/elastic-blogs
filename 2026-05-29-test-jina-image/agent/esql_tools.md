# Agent Builder Tools — Search Template 定義集 (v1 アーキテクチャ)

> Elastic Agent Builder ("Agents" 画面) に登録するための、3 つの検索ツールの定義集。
> 設計の鍵は **`query_vector_builder`** — Elastic が _search リクエストの中で
> _inference を呼んでくれるので、Python は要らない。

## なぜ Search Template か (ES|QL ではなく)

ES|QL の `KNN` 関数は `query_vector` (生の数値配列) を要求するため、テキストクエリから
ベクトルを作る部分は表現できない。Search Template は普通の DSL なので、
`query_vector_builder` をそのまま使える。Search Template も Elastic-native で、
Python wrapper を挟まずに済む。

## 前提: 既存のインデックスとマッピング

- alias: `image-search-poc` (= `.env` の `INDEX_NAME`)
- 実体: `image-search-poc-v1`
- 関連フィールド:
  - `image_embedding` … dense_vector(1024) / cosine / int8_hnsw
  - `image_key`       … keyword (S3 オブジェクトキー、ドキュメント `_id` でもある)
  - `name`            … text (拡張子抜きのファイル名)

---

## 一回だけ: Dev Tools で 3 つの Search Template を登録する

### Tool 1: search_by_text (自然言語クエリ → 上位3枚)

```http
PUT _scripts/search_by_text
{
  "script": {
    "lang": "mustache",
    "source": {
      "size": 3,
      "_source": ["image_key", "name"],
      "query": {
        "knn": {
          "field": "image_embedding",
          "k": 3,
          "num_candidates": 50,
          "query_vector_builder": {
            "embedding": {
              "inference_id": ".jina-embeddings-v5-omni-small",
              "input": {
                "type": "text",
                "value": "{{query}}"
              }
            }
          }
        }
      }
    }
  }
}
```

呼び出し例 (Dev Tools で動作確認):

```http
GET image-search-poc/_search/template
{
  "id": "search_by_text",
  "params": {
    "query": "赤い椅子"
  }
}
```

### Tool 2: search_by_text_in_image (画像内文字 → 上位3枚)

中身は Tool 1 と同じ Search Template。エージェントが呼ぶときに
`query` パラメータに整形プロンプト `an image containing the visible text 'X'` を入れる。
新しい template を作る必要はなく、Tool 1 を使い回す。

呼び出し例:

```http
GET image-search-poc/_search/template
{
  "id": "search_by_text",
  "params": {
    "query": "an image containing the visible text 'SOLD'"
  }
}
```

### Tool 3: search_by_filename (類似画像検索)

```http
PUT _scripts/search_by_filename
{
  "script": {
    "lang": "mustache",
    "source": {
      "size": 3,
      "_source": ["image_key", "name"],
      "query": {
        "bool": {
          "must_not": [
            { "term": { "image_key": "{{image_key}}" } }
          ],
          "must": [
            {
              "knn": {
                "field": "image_embedding",
                "k": 4,
                "num_candidates": 50,
                "query_vector_builder": {
                  "lookup": {
                    "index": "image-search-poc",
                    "id": "{{image_key}}",
                    "path": "image_embedding"
                  }
                }
              }
            }
          ]
        }
      }
    }
  }
}
```

呼び出し例:

```http
GET image-search-poc/_search/template
{
  "id": "search_by_filename",
  "params": {
    "image_key": "poc-uploads/IMG_8133.jpeg"
  }
}
```

---

## Agent Builder への登録

1. Kibana 左メニュー → **Agents** → エージェントを開く → **Tools** タブ → **Add tool**
2. Tool type: **Search Template** (もし選べる場合) または **Custom search**
3. 各ツールに対して以下を設定:

| Tool name              | Template ID         | Parameters                                                 | Description                                                                |
| ---------------------- | ------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| `search_by_text`       | `search_by_text`    | `query` (string)                                           | 自然言語のクエリで画像を検索 (上位3件)                                  |
| `search_by_text_in_image` | `search_by_text` | `query` (string)                                           | エージェントは「an image containing the visible text 'X'」の形に整形すること |
| `search_by_filename`   | `search_by_filename`| `image_key` (string, ex. `poc-uploads/IMG_8133.jpeg`)      | 既存画像と類似の画像を 3 件返す (自分自身は除く)                            |

4. Agent の "Instructions" には `agent/system_prompt.md` の内容を貼る

---

## image_key → pre-signed URL の変換 (画像表示用)

Search Template の結果には `image_key` だけが入っている (S3 のオブジェクトキー)。
Agent Builder のチャットで画像を inline 表示するには、これを **pre-signed URL** に変換する
必要がある。3 通り:

| やり方                                                                        | 良いところ                              | 注意                                                                  |
| ----------------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------- |
| (a) `tools/search_tools.py` の `make_presigned_url()` を呼ぶ Python ツールを追加で公開 | 安全 (短時間 URL)                          | Python wrapper が要る                                                |
| (b) ingest 時に 24h 有効の URL を index に持たせる                           | Search Template だけで完結               | 24h ごとに ingest しないと URL が切れる                              |
| (c) S3 バケットを CloudFront 経由で公開する                                  | 永続 URL                                  | バケットは結局 public に近くなる (CLAUDE.md のセキュリティ要件に反す) |

PoC では **(a)** を採用するのがバランス的に楽。`search_tools.py` をそのまま再利用可。
詳しくは Phase 5 の system prompt で「結果の image_key を受け取ったら make_presigned_url で
URL を生成する」と書く案も可能。

---

## まとめ

| 何をするか                       | 何を使うか                                  |
| -------------------------------- | ------------------------------------------- |
| テキスト検索 (上位3画像)         | Search Template `search_by_text`            |
| 画像内文字検索                   | 上と同じ template + プロンプト整形          |
| ファイル名から類似画像検索       | Search Template `search_by_filename`        |
| ベクトル化 (テキスト or 画像)    | `query_vector_builder.embedding` (Elastic が自動) |
| 似ている画像探し                 | `query_vector_builder.lookup` (Elastic が自動) |
| 画像表示用 URL                  | `tools/search_tools.py` の `make_presigned_url`  |

Python 側に残るのは `make_presigned_url` だけ。検索ロジックはすべて Elastic 側で完結する。
