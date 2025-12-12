# エイリアスの作成

```
POST _aliases
{
  "actions": [
    {
      "add": {
        "index": "sales_data_*",
        "alias": "sales_data"
      }
    },
    {
      "add": {
        "index": "hr_data_*",
        "alias": "hr_data"
      }
    }
  ]
}
```
