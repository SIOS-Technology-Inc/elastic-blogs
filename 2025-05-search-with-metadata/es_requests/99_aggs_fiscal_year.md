# 事業年度一覧の取得リクエスト

```
GET /sios_securities_report/_search
{
    "size": 0,
    "aggs": {
        "year": {
            "terms": {
              "field": "meta.fiscal_year"
            }
        }
    }
}
```
