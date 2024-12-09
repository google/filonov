# How to use media-tagger as a library

1. Install `media-tagger` with `pip install media-tagging` command.

2. Import package modules

```
from media_tagging import tagger, writer
```

3. Initialize `media_tagger`:

```
YOUR_TAGGER_TYPE='gemini-image'
media_tagger = tagger.create_tagger(YOUR_TAGGER_TYPE)
```

4. Perform media_tagging:

```
PATH_TO_MEDIA=['/path/to/media1.jpg', '/path/to/media2.jpg']
result = media_tagger.tag_media(media_paths=PATH_TO_MEDIA)
```

You can optionally pass `tagging_parameters` dictionary to customize tagging.
I.e. if you want to get 100 tags (instead of default 10) you can specify n_tags=10 in `tagging_parameters`.

```
tagging_parameters = {'n_tags': 100}
result = media_tagger.tag_media(
  media_paths=PATH_TO_MEDIA,
  tagging_parameters=tagging_parameters
)
```

5. Save result of tagging to JSON or CSV

```
writer.create_writer('json').write(result, 'tagging_output')
writer.create_writer('csv').write(result, 'tagging_output')
```
