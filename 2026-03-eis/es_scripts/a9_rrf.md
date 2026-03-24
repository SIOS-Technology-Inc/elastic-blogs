# RRF リランクのテスト

下記を行うクエリーを ES|QL を使って記述する。

- ベクトル検索結果20件とキーワード検索結果20件をRRFを使ってリランクし、上位10件のみとする。
  - ベクトル検索には、.jina-embeddings-v5-text-nano を利用する。

```
POST /_query
{
  "query": """
FROM waganeko METADATA _score, _id, _index
| FORK (WHERE KNN(content_embedding, TEXT_EMBEDDING(?query, ".jina-embeddings-v5-text-nano")) | SORT _score DESC | LIMIT 20)
       (WHERE MATCH(content, ?query) | SORT _score DESC | LIMIT 20)
| DROP content_embedding
| FUSE
| KEEP chunk_no, content, _score
| SORT _score DESC
| LIMIT 10
""",
  "params": [
    { "query": "吾輩が生まれた場所は?" }
  ]
}
```


検索結果

```
...
  "values": [
    [
      1462,
      "今日何人あばたに出逢って、その主は男か女か、その場所は小川町の勧工場であるか、上野の公園であるか、ことごとく彼の日記につけ込んである。彼はあばたに関する智識においては決して誰にも譲るまいと確信している。せんだってある洋行帰りの友人が来た折なぞは、「君西洋人にはあばたがあるかな」と聞いたくらいだ。",
      0.028958333333333336
    ],
    [
      2,
      "どこで生れたかとんと見当がつかぬ。何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。吾輩はここで始めて人間というものを見た。しかもあとで聞くとそれは書生という人間中で一番獰悪な種族であったそうだ。この書生というのは時々我々を捕えて煮て食うという話である。しかしその当時は何という考もなかったから別段恐しいとも思わなかった。",
      0.01639344262295082
    ],
    ...
]
...
```
