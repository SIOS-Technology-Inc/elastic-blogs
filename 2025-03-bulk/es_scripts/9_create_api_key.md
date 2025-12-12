# API Key の作成

```
POST /_security/api_key
{
   "name": "kakinosuke_write_api_key",
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
