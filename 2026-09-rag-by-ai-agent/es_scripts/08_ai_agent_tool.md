# AI Agent Tool

Create new tool 画面で下記のように登録します。

## Type

- Type : ES|QL

- ES|QL Query : 下記を入力

（セマンティックリランク用クエリーをAI Agent Tool用に修正した内容）

```
FROM kakinosuke_202609* METADATA _score, _id, _index
| FORK (WHERE MATCH(content.semantic, ?query) | SORT _score DESC | LIMIT 10)
       (WHERE MATCH(content, ?query) | SORT _score DESC | LIMIT 10)
| FUSE RRF
| KEEP chunk_no, content, _score
| SORT _score DESC
| LIMIT 10
| RERANK ?query ON content WITH { "inference_id" : ".jina-reranker-v3.5" }
| SORT _score DESC
| LIMIT 5
```

- ES|QL Parameters
  <br>Infer a parameter をクリックします。

  - Name : query （自動表示されます）

  - Description : 検索したい内容

  - Type : string （自動表示されます）

  - Optional : false

## Details

- Tool ID : kakinosuke.get_contents

- Description : 下記を入力する

```
kakinosuke_202609 インデックスに対して、キーワード検索とセマンティック検索を行い、RRFで結果を統合したあと、セマンティックリランクで質問に近い順に並べ直し、上位5件の本文チャンクを返す。
```

## Labels

- Lables : kakinosuke

---

## \[Save & test \] を押して tool を保存し、テストを開始します。

- query : "柿之助の3人の家来は?"

と入力し、\[→ Submit\] をクリックします。

実行結果が表示されます。

