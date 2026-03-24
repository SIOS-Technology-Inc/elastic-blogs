# README.md

Elasticsearch の Dev Tools の Console 上で実行する各種スクリプト

| ファイル | 説明 | 備考 |
|---|---|---|
| [a1_upload_ndjson.md](./a1_upload_ndjson.md) | NDJSONファイルのアップロード | 手順の概略のみ。スクリプトなし。 |
| [a2_create_index.md](./a2_create_index.md) | waganeko_2026_03 インデックスの作成 | icu, kuromoji の設定を含む。 |
| [a3_create_index_mapping.md](./a3_create_index_mapping.md) | waganeko_2026_03 インデックスへのフィールドの作成 | 密ベクトル用のフィールドなどを作成する。 |
| [a4_create_alias.md](./a4_create_alias.md) | waganeko_2026_03 インデックスへのエイリアスの作成 | |
| [a5_create_ingest_pipeline.md](./a5_create_ingest_pipeline.md) | 密ベクトル生成用のパイプラインの作成 | .jina-embedding-v5-text-nano を利用する。 |
| [a6_reindex.md](./a6_reindex.md) | waganeko_tmp -&gt; waganeko インデックスへの reindex | 密ベクトル生成用の pipeline を経由する。 |
| [a7_keyword_search.md](./a7_keyword_search.md) | キーワード検索 | 形態素解析を行った上で、キーワード検索を行う。 |
| [a8_vector_search.md](./a8_vector_search.md) | ベクトル検索 | .jina-embeddings-v5-text-nano を利用して密ベクトル検索を行う。 |
| [a9_rrf.md](./a9_rrf.md) | キーワード検索とベクトル検索の RRF リランク | ES&#124;QL の FUSE を利用して RRF リランクを行う。 |
| [a10_rrf_semantic_rerank.md](./a10_rrf_semantic_rerank.md) | RRF リランク後にセマンティックリランクを実施 | .jina-reranker-v3 を利用する。 |
| [a11_completion.md](./a11_completion.md) | LLM への問い合わせ | セマンティックリランク後の上位1位のドキュメントをベースに .openai-gpt-oss-120b-completion に問い合わせ。 |
| README.md | このファイル | |

