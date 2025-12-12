インデックスエイリアス作成リクエスト

```
POST _aliases
{
  "actions": [
    {
      "add": {
        "index": "medicine_20250415",
        "alias": "medicine"
      }
    }
  ]
}
```
