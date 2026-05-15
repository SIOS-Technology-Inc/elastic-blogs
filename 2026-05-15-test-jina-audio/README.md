# test-jina-audio - スクリプト解説

このリポジトリは **Elasticsearch + Jina Embeddings v5 (omni)** を使った音声検索 PoC です。
日本語の音声を 1024 次元のベクトルに変換して Elasticsearch にインデックスし、
**テキスト → 音声検索** や **音声 → 音声検索** ができることを検証しています。

---

## 全体像

このプロジェクトには2つの実験ストリームがあります。

| ストリーム | 目的 | インデックス名 |
|---|---|---|
| **カスタマーサポート音声** | 1〜5.wav の問い合わせ音声を意味検索 | `audio-poc-jina-v5` または `audio-poc-jina-eis-v1` |
| **データセンター音声** | YouTube動画の音声で長時間データの検索を試す | `audio-poc-datacenter` |

それぞれ「**インデックス（登録）**」と「**サーチ（検索）**」のスクリプトが分かれています。


すべてのスクリプトは `.env` から接続情報を読み込みます。

```env
ES_URL=https://localhost:9200
ES_USER=elastic
ELASTIC_PASSWORD=あなたのパスワード
INDEX_NAME=audio-poc-jina-v5
INFERENCE_ID=.jina-embeddings-v5-omni-small
```

## 各 Python ファイルの役割

### インデックス系（音声をベクトル化して Elasticsearch に登録）

#### [index_audio_eis.py](index_audio_eis.py)
- **役割:** `index_audio_poc.py` と同じ処理を **`elasticsearch-py` ライブラリ** で実装した版
- **特徴:**
  - curl ではなく公式 Python クライアントを使うので、Python らしい書き方
  - `INDEX_NAME` はファイル内ハードコード（`audio-poc-jina-eis-v1`）
  - 同じ音声・同じモデルを使うので、結果はほぼ同じになるはず（比較用）

---

### サーチ系（クエリで音声を検索）

#### [search_audio_poc.py](search_audio_poc.py) — **テキスト → 音声検索**
- **役割:** 日本語テキストをクエリにして、近い音声を kNN 検索
- **流れ:**
  1. ユーザーが日本語クエリを入力（例: 「パスワードが分からない」）
  2. テキストを Jina で 1024 次元ベクトルに変換
  3. Elasticsearch でベクトル類似検索（上位 3 件）
- **使うインデックス:** `.env` の `INDEX_NAME`

#### [search_audio_by_audio.py](search_audio_by_audio.py) — **音声 → 音声検索**
- **役割:** **音声ファイル** をクエリにして、近い音声を検索
- **流れ:**
  1. ユーザーが音声ファイル名を入力（例: `1.wav`）
  2. その音声を Jina でベクトルに変換
  3. Elasticsearch でベクトル類似検索（上位 5 件）
- **用途:** 「似た問い合わせ音声を探す」など、音声同士のマッチング検証

## Audio Sample Files

音声ファイルはプライバシー・機密情報保護の観点から、本リポジトリには含めていません。

各自で `audio-samples` フォルダを作成し、検証用の音声ファイルを配置してください。

例：

```text
2026-05-15-test-jina-audio/
├── audio-samples/
│   ├── 1.wav
│   ├── 2.wav
│   └── ...
├── index_audio_eis.py
├── search_audio_poc.py
└── search_audio_by_audio.py
