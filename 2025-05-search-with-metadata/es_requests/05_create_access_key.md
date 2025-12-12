# 読み取り用 Access Key の作成リクエスト

```
POST /_security/api_key
{
  "name": "sios_securities_report_read",
  "role_descriptors": {
    "sios_securities_report_read": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["sios_securities_report*"],
          "privileges": ["read"]
        }
      ]
    }
  }
}
```

