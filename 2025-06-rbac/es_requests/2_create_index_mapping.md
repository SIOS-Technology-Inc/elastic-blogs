# Create index mapping

あくまでもアクセス権の確認のためのインデックスなので、形態素解析については省略します。

```
PUT /sales_data_2024/_mapping
{
  "properties": {
    "@timestamp": {
      "type": "date"
    },
    "content": {
      "type": "text"
    }
  }
}

PUT /sales_data_2025/_mapping
{
  "properties": {
    "@timestamp": {
      "type": "date"
    },
    "content": {
      "type": "text"
    }
  }
}

PUT /hr_data_2024/_mapping
{
  "properties": {
    "@timestamp": {
      "type": "date"
    },
    "content": {
      "type": "text"
    }
  }
}

PUT /hr_data_2025/_mapping
{
  "properties": {
    "@timestamp": {
      "type": "date"
    },
    "content": {
      "type": "text"
    }
  }
}
```
