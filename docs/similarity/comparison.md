## Comparing two media

Somethings it's useful to understand why two media end up in the same or different clusters.

`media-similarity` can provide detailed information how two media as similar to each other.

> Please note that this requires [persistence setup](persistence.md).



/// tab | cli
```
media-similarity compare image1 image2 image3 \
  --media-type IMAGE \
  --db-uri=<CONNECTION_STRING>
```
///

/// tab | python

```python
from media_similarity import MediaSimilarityComparisonRequest, MediaSimilarityService

service = MediaSimilarityService.from_connecting_string(
  'sqlite:///tagging_results.db'
)

request = MediaSimilarityComparisonRequest(
  media_paths=[
    'image1.png',
    'image2.png',
    'image3.png',
    ],
    media_type='IMAGE',
)

compared_media = service.compare_media(request)
```
///
