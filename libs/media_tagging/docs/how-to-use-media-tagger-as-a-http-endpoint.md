# How to use media-tagger as a HTTP endpoint

`media-tagger` can be exposed as HTTP endpoint.

1. Install `media-tagger` with `pip install media-tagging[server]` command.

2. Start server
```
python -m media_tagging.entrypoints.server
```
> By default you start application on localhost:8000. If you want to start on a
> different host and port specify --host HOSTNAME --port PORT.

3.  Tag media
(check examples using [`httpie`](https://httpie.io/docs/cli) below):

```
http POST localhost:8000/media_tagging/tag \
  media_paths[]=<PATH_TO_MEDIA> \
  tagger_type=<TYPE_OF_TAGGER> \
  media_type=<TYPE_OF_TAGGER> \
  tagging_options][n_tags]=<NUMBER_OF_TAGS>
```

Tag file on GCS:

```
http POST localhost:8000/media_tagging/tag \
  media_paths[]=gs://bucket/image.png \
  tagger_type=gemini \
  media_type=IMAGE
```

4.  Describe media

```
http POST localhost:8000/media_tagging/describe \
  media_paths[]=<PATH_TO_MEDIA> \
  tagger_type=<TYPE_OF_TAGGER> \
  media_type=<TYPE_OF_TAGGER> \
  tagging_options][n_tags]=<NUMBER_OF_TAGS>
```

Tag file on GCS using custom prompt:

```
http POST localhost:8000/media_tagging/describe \
  media_paths[]=gs://bucket/image.png \
  tagger_type=gemini \
  media_type=IMAGE \
  tagging_options][custom_prompt]=<YOUR_PROMPT_HERE>
```
