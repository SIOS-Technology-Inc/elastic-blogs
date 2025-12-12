# Create API Key 

## user1_api_key_20250702

```
POST /_security/api_key
{
  "name": "user1_api_key_20250702",
  "expiration": "1d",
  "role_descriptors": {
    "dls_sample_user1": {
      "cluster": ["monitor"],
      "index": [
        {
          "names": [
            "dls_sample_202507"
          ],
          "privileges": [
            "read"
          ],
          "query": {
            "template": {
              "params": {
                "access_control": [
                  "user1@example.com",
                  "group1"
                ]
              },
              "source": """
              {
                "bool": {
                  "should": [
                    {
                      "bool": {
                        "must_not": {
                          "exists": {
                            "field": "_allow_access_control"
                          }
                        }
                      }
                    },
                    {
                      "terms": {
                        "_allow_access_control.enum": {{#toJson}}access_control{{/toJson}}
                      }
                    }
                  ]
                }
              }
              """
            }
          }
        }
      ]
    }
  }
}
```

## user2_api_key_20250702

```
POST /_security/api_key
{
  "name": "user2_api_key_20250702",
  "expiration": "1d",
  "role_descriptors": {
    "dls_sample_user2": {
      "cluster": ["monitor"],
      "index": [
        {
          "names": [
            "dls_sample_202507"
          ],
          "privileges": [
            "read"
          ],
          "query": {
            "template": {
              "params": {
                "access_control": [
                  "user2@example.com",
                  "group2"
                ]
              },
              "source": """
              {
                "bool": {
                  "should": [
                    {
                      "bool": {
                        "must_not": {
                          "exists": {
                            "field": "_allow_access_control"
                          }
                        }
                      }
                    },
                    {
                      "terms": {
                        "_allow_access_control.enum": {{#toJson}}access_control{{/toJson}}
                      }
                    }
                  ]
                }
              }
              """
            }
          }
        }
      ]
    }
  }
}
```

## user3_api_key_20250702

```
POST /_security/api_key
{
  "name": "user3_api_key_20250702",
  "expiration": "1d",
  "role_descriptors": {
    "dls_sample_user3": {
      "cluster": ["monitor"],
      "index": [
        {
          "names": [
            "dls_sample_202507"
          ],
          "privileges": [
            "read"
          ],
          "query": {
            "template": {
              "params": {
                "access_control": [
                  "user3@example.com",
                  "group1"
                ]
              },
              "source": """
              {
                "bool": {
                  "should": [
                    {
                      "bool": {
                        "must_not": {
                          "exists": {
                            "field": "_allow_access_control"
                          }
                        }
                      }
                    },
                    {
                      "terms": {
                        "_allow_access_control.enum": {{#toJson}}access_control{{/toJson}}
                      }
                    }
                  ]
                }
              }
              """
            }
          }
        }
      ]
    }
  }
}
```


## user4_api_key_20250702

```
POST /_security/api_key
{
  "name": "user4_api_key_20250702",
  "expiration": "1d",
  "role_descriptors": {
    "dls_sample_user4": {
      "cluster": ["monitor"],
      "index": [
        {
          "names": [
            "dls_sample_202507"
          ],
          "privileges": [
            "read"
          ],
          "query": {
            "template": {
              "params": {
                "access_control": [
                  "user4@example.com",
                  "group2"
                ]
              },
              "source": """
              {
                "bool": {
                  "should": [
                    {
                      "bool": {
                        "must_not": {
                          "exists": {
                            "field": "_allow_access_control"
                          }
                        }
                      }
                    },
                    {
                      "terms": {
                        "_allow_access_control.enum": {{#toJson}}access_control{{/toJson}}
                      }
                    }
                  ]
                }
              }
              """
            }
          }
        }
      ]
    }
  }
}
```

上記の4つの API Key が対応するユーザー、グループをまとめると以下の表になります。

| API Key 名 | ユーザー、グループ | 有効期限 |
|---|---|---|
| user1_api_key_20250702 | user1@example.com, group1 | 1日 |
| user2_api_key_20250702 | user2@example.com, group2 | 1日 |
| user3_api_key_20250702 | user3@example.com, group1 | 1日 |
| user4_api_key_20250702 | user4@example.com, group2 | 1日 |


## 備考

ここでは、わかりやすく、Dev Tools の Console から API Key の生成リクエストを発行する方法を採用しています。

なお、

https://www.elastic.co/docs/reference/search-connectors/es-dls-e2e-guide

の例では、.search-acl-filter-source1 および .search-acl-filter-source2 インデックスに
各ユーザーごとの権限情報を1ドキュメントとして格納しています。

その内容（権限情報）を GET /index-name/_doc/userId で取得しています。

取得した内容（権限情報）を元に Create API Key を行い、一時的な API Key を生成しています。


