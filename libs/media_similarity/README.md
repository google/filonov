# Media similarity

*This is not an officially supported Google product.*

1. Install

```
pip install media-similarity
```

2. Run `media-similarity` with one of two currently supported actions: `cluster` and `search`:

* `cluster` will take several media, tag them and combined them into clusters.

```
media-similarity cluster <PATH_TO_MEDIA> \
  --tagger=<TAGGER_TYPE> \
  --db-uri=<CONNECTION_STRING>
```

* `search` will find top similar media for a given seed media.

```
media-similarity search <SEED_MEDIA_PATH> \
  --db-uri=<CONNECTION_STRING>
```
