# 読み取り用 API Key 作成リクエスト

検索時に利用する API Key を発行するためのリクエスト。

## request for sales_user

```
POST /_security/api_key
{
  "name": "sales_user_20250616",
  "expiration": "10d",
  "role_descriptors": {
    "sales_data_read": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["sales_data*"],
          "privileges": ["read"]
        }
      ]
    }
  }
}
```

response

```
{
  "id": "*******************",
  "name": "sales_data_read",
  "expiration": 1752387594021,
  "api_key": "*******************",
  "encoded": "**********************************************=="
}
```

encoded の値を、config.yaml へ転記します。

## request for hr_user

```
POST /_security/api_key
{
  "name": "hr_user_20250616",
  "expiration": "10d",
  "role_descriptors": {
    "hr_data_read": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["hr_data*"],
          "privileges": ["read"]
        }
      ]
    }
  }
}
```

response

```
{
  "id": ""*******************",
  "name": "hr_data_read",
  "expiration": 1750662367767,
  "api_key": "*******************",
  "encoded": "**********************************************=="
}
```

encoded の値を、config.yaml へ転記します。

## request for sales_and_hr_user

```
POST /_security/api_key
{
  "name": "sales_and_hr_user_20250616",
  "expiration": "10d",
  "role_descriptors": {
    "sales_and_hr_data_read": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["sales_data*", "hr_data*"],
          "privileges": ["read"]
        }
      ]
    }
  }
}
```

response

```
{
  "id": "*******************",
  "name": "sales_and_hr_data_read",
  "expiration": 1750662367767,
  "api_key": "*******************",
  "encoded": "**********************************************=="
}
```

encoded の値を、config.yaml へ転記します。

---

今回は簡易な動作検証のため、"expiration":"10d" を指定していますが、
本番運用では適切な値に設定することを推奨します。

また、今回は簡易なサンプルなので、あらかじめ Dev Tools の Console で
上記リクエストを発行し、API Key を作成していますが、
ログインするたびに上記のリクエストを発行し、有効期限が短い API Key を生成する方法も考えられます。

ただし、そのような仕組みにしようとすると、ここで説明するには複雑な構成になってしまうため、
ここでは簡易的な仕組みとしています。

※API Key を発行するためには、その権限（manage_api_key）を持ったユーザーをあらかじめ作成しておく必要があります。
また、そのユーザーに接続するには API Key ではなく、user / password による認証が必要です。

