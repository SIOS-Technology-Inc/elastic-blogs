# Access Key の作成

## 読み取り用 Access Key の作成

```
POST /_security/api_key
{
  "name": "medicine_read",
  "role_descriptors": {
    "medication_read": {
      "cluster": ["all"],
      "indices": [
        {
          "names": ["medicine*"],
          "privileges": ["read"]
        }
      ]
    }
  }
}
```
