# インデックスエイリアス作成リクエスト

```
POST _aliases
{
  "actions": [
    {
      "add": {
        "index": "kakinosuke_202505",
        "alias": "kakinosuke"
      }
    }
  ]
}
```

※すでに "kakinosuke" というエイリアスがある場合は、
以前のエイリアスを削除するか、もしくは、
今回作成するエイリアスの名称を違う名前にしてください。
