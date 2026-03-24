# Reindex

## reindex

```
POST _reindex?wait_for_completion=false
{
  "source": {
    "index": "waganeko_tmp"
  },
  "dest": {
    "index": "waganeko",
    "pipeline": "eis_jina_embeddings_pipeline"
  }
}
```

## check completion

```
GET /_tasks/<TASK_ID>
```

## refresh

```
POST /waganeko/_refresh
```

