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

Suppose we want to tag images via Gemini
```
PATH_TO_MEDIA=['/path/to/media1.jpg', '/path/to/media2.jpg']
result = media_tagger.tag_media(
  media_paths=PATH_TO_MEDIA,
  tagger_type='gemini',
  media_type='IMAGE',
)
```

You can optionally pass `tagging_parameters` dictionary to customize tagging.

* Customize number of tags

  If you want to get 100 tags (instead of default 10) you can specify `n_tags=100` in `tagging_parameters`.

  ```
  tagging_parameters = {'n_tags': 100}
  result = media_tagger.tag_media(
    media_paths=PATH_TO_MEDIA,
    tagger_type='gemini',
    media_type='IMAGE',
    tagging_parameters=tagging_parameters,
  )
  ```

* Search for particular tags

  If you want to only to find such tags as  *cat*, *dog*, *bird* you can specify `tags=['cat', 'dog', 'bird']` in `tagging_parameters`.

  ```
  tagging_parameters = {'tags': ['cat', 'dog', 'bird']}
  result = media_tagger.tag_media(
    media_paths=PATH_TO_MEDIA,
    tagger_type='gemini',
    media_type='IMAGE',
    tagging_parameters=tagging_parameters,
  )
  ```
5. Perform media description:

Media can also be described. Suppose we want to describe two images via Gemini
```
PATH_TO_MEDIA=['/path/to/media1.jpg', '/path/to/media2.jpg']
result = media_tagger.describe_media(
  media_paths=PATH_TO_MEDIA,
  tagger_type='gemini',
  media_type='IMAGE',
)
```

You can optionally pass `custom_prompt` to `tagging_parameters` dictionary to customize description.

```
tagging_parameters = {'custom_prompt': 'Is this an advertising? Answer only True or False'}
result = media_tagger.describe_media(
  media_paths=PATH_TO_MEDIA,
  tagger_type='gemini',
  media_type='IMAGE',
  tagging_parameters=tagging_parameters,
)
```

6. Save result of tagging to local or remote storage with `garf-io`

I.e. to save results to csv file run the following

```
import garf_io import writer


report = media_tagging.tagging_result.convert_tagging_results_to_garf_report(
  result
)
writer.create_writer('csv').write(report, 'tagging_results')
```
