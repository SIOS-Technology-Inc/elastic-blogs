# 書き込み用 Access Key の作成リクエスト

```
POST /_security/api_key
{
  "name": "kakinosuke_write",
  "expiration": "1d",
  "role_descriptors": {
    "kakinosuke_write_role": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["kakinosuke*"],
          "privileges": ["all"]
        }
      ]
    }
  }
}
```

返却される encoded の値を、.env に転記します。

最初しか使用しないので、expiration : '1d' を設定しておきます。

Expire された後に、再度、利用したい場合は Access Key を再作成してください。

参考URL:

https://www.elastic.co/guide/en/elasticsearch/reference/8.18/security-api-create-api-key.html

https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-security-create-api-key


# 読み取り用 Access Key の作成リクエスト

```
POST /_security/api_key
{
  "name": "kakinosuket_read",
  "role_descriptors": {
    "kakinosuke_read_role": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["kakinosuke*"],
          "privileges": ["read"]
        }
      ]
    }
  }
}
```

返却される encoded の値を、.env に転記します。

