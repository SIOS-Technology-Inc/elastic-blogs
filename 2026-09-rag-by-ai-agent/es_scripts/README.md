# README.md

このフォルダには、Elasticsearch 上で発行するリクエストをまとめています。

手順の詳細は、[../README.md](../README.md) も併せて参照してください。

| ファイル名 | 説明 |
|---|---|
| [01_create_index.md](./01_create_index.md) | kakinosuke_202609 インデックスを作成する。 |
| [02_put_mapping.md](./02_put_mapping.md) | kakinosuke_202609 インデックスに mapping を追加する。 |
| [03_reindex.md](./03_reindex.md) | kakinosuke_tmp インデックスをkakinosuke_202609 インデックスへ reindex する。 |
| [04_keyword_search.md](./04_keyword_search.md) | kakinosuke_202609 インデックスに対し、キーワード検索を行う。 |
| [05_semantic_search.md](./05_semantic_search.md) | kakinosuke_202609 インデックスに対し、セマンティック検索を行う。 |
| [06_hybrid_search.md](./06_hybrid_search.md) | kakinosuke_202609 インデックスに対し、キーワード検索とセマンティック検索を行い、RRF でリランクする。 |
| [07_semantic_rerank.md](./07_semantic_rerank.md) | kakinosuke_202609 インデックスに対しハイブリッド検索を行った結果を、セマンティックリランカーでリランクする。 |
| [08_ai_agent_tool.md](./08_ai_agent_tool.md) | AI Agent Tool を作成する。 |
| [09_ai_agent.md](./09_ai_agent.md) | AI Agent を作成する。 |
