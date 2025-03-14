# How to use media-tagger as a library

1. Install `media-tagger` with `pip install media-tagging` command.

2. Import `media_tagging`

```
import media_tagging
```

3. Initialize `MediaTaggingService`:

```
media_tagger = MediaTaggingService()
```
If you want to persist results of tagging provide repository to `MediaTaggingService`

```
from media_tagging import repositories


DB_CONNECTION_STRING=sqlite:///tagging.db

media_tagger = MediaTaggingService(
  repo=repositories.SqlAlchemyTaggingResultsRepository(DB_CONNECTION_STRING)
)
```

4. Perform media_tagging:

Suppose we want to tag images via gemini
```
PATH_TO_MEDIA=['/path/to/media1.jpg', '/path/to/media2.jpg']
result = media_tagger.tag_media(
  media_paths=PATH_TO_MEDIA,
  tagger_type='gemini',
  media_type='IMAGE',
)
```

You can optionally pass `tagging_parameters` dictionary to customize tagging.
I.e. if you want to get 100 tags (instead of default 10) you can specify `n_tags=100` in `tagging_parameters`.

```
tagging_parameters = {'n_tags': 100}
result = media_tagger.tag_media(
  media_paths=PATH_TO_MEDIA,
  tagger_type='gemini',
  media_type='IMAGE',
  tagging_parameters=tagging_parameters,
)
```

5. Save result of tagging to local or remote storage with `garf-io`

I.e. to save results to csv file run the following

```
import garf_io import writer


report = media_tagging.tagging_result.convert_tagging_results_to_garf_report(
  result
)
writer.create_writer('csv').write(report, 'tagging_results')
```
