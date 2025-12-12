# Create Documents

```
POST /dls_sample_202507/_doc
{
  "content": "doc1: This document can be read by user1 or group1.",
  "_allow_access_control": [
    "user1@example.com",
    "group1"
  ]
}

POST /dls_sample_202507/_doc
{  "content": "doc2: This document can be read by user2 or group2.",
  "_allow_access_control": [
    "user2@example.com",
    "group2"
  ]
}

POST /dls_sample_202507/_doc
{
  "content": "doc3: This document can be read by user1.",
  "_allow_access_control": [
    "user1@example.com"
  ]
}

POST /dls_sample_202507/_doc
{
  "content": "doc4: This document can be read by user2.",
  "_allow_access_control": [
    "user2@example.com"
  ]
}

POST /dls_sample_202507/_doc
{
  "content": "doc5: This document can be read by group1.",
  "_allow_access_control": [
    "group1"
  ]
}

POST /dls_sample_202507/_doc
{
  "content": "doc6: This document can be read by group2.",
  "_allow_access_control": [
    "group2"
  ]
}

POST /dls_sample_202507/_doc
{
  "content": "doc7: This document can be read by everybody."
}
```

---

上記の7つのドキュメントの読み取り権限をまとめると以下の表になります。

| ドキュメントの内容 | 読み取り可能なユーザー名、グループ名 |
|---|---|
| doc1: ... | user1@example.com または group1 |
| doc2: ... | user2@example.com または group2 |
| doc3: ... | user1@example.com |
| doc4: ... | user2@example.com |
| doc5: ... | group1 |
| doc6: ... | group2 |
| doc7: ... | 全員 |
