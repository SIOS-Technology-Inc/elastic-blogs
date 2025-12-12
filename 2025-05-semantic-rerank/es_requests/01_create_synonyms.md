# 同義語の登録

```
PUT _synonyms/kakinosuke_synonyms_set
{
  "synonyms_set": [
    {
      "synonyms": "おむすび,おにぎり"
    }
  ]
}
```

kakinosuke_synonyms_set という名前の synonym set に

"おむすび,おにぎり"

の同義語を登録します。
