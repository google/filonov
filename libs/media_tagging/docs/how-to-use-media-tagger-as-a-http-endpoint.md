# How to use media-tagger as a HTTP endpoint

`media-tagger` can be exposed as HTTP endpoint.

1. Install `media-tagger` with `pip install media-tagging` command.

2. Clone `media-tagging` repository and run:

```
fastapi run entrypoints/server.py
```
> By default you start application on localhost:8000. If you want to start on a
> different host and port specify --host HOSTNAME --port PORT.

3.  Categorize media
(check examples using [`httpie`](https://httpie.io/docs/cli) below):

* via Google Cloud Vision API:
POST to `http://localhost:8000/tagger/api`

```
http POST localhost:8000/tagger/api \
  data[media_url]=<PATH_TO_MEDIA> \
  data[tagging_options][n_tags]=<NUMBER_OF_TAGS>
```

* via Google Gemini API:
POST to `http://localhost:8000/tagger/llm`

```
http POST localhost:8000/tagger/llm \
  data[media_url]=<PATH_TO_MEDIA> \
  data[tagging_options][n_tags]=<NUMBER_OF_TAGS>
```
