## Searching for similar media

`media-similarity` can search for similar media given a set of seed media.

> Please note that this requires persistence setup.



/// tab | cli
```
media-similarity search image3 \
  --media-type IMAGE \
  --db-uri=<CONNECTION_STRING>
```
///

/// tab | python

```python
from media_similarity import MediaSimilaritySearchRequest, MediaSimilarityService

service = MediaSimilarityService.from_connecting_string(
  'sqlite:///tagging_results.db'
)

request = MediaSimilaritySearchRequest(
  media_paths=[
    'image3.png',
    ],
    media_type='IMAGE',
    n_results=1,
)

similar_media = service.find_similar_media(request)
```
///

### Working with similarity search results  (TODO)

Once `find_similar_media` is executed you get a `SimilaritySearchResults` object which contains:

* via `.` property as a dict
* via `.to_garf_report` method as a GarfReport

