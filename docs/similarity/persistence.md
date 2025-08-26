# Persisting Similarity Results

By default when analyzing media similarity all intermediate data is saved in the memory.

You can opt-in to persisting data in the database of your choice.

If you're analyzing similarity of the same [media pair](media-iair.md) for the second time its similarity information will be fetched
from DB instead of performing actual similarity calculation.

## Using shared database

The easiest option is to use a single database for tagging and similarity results.

/// tab | cli
```bash
media-similarity cluster image1.png image2.png image3.png \
  --media-type IMAGE \
  --tagger gemini \
  --db-uri sqlite:///tagging.db
```
///

/// tab | python
```python
from media_similarity import MediaClusteringRequest, MediaSimilarityService
from media_similarity.repositories import SqlAlchemySimilarityResultsRepository

repository = SqlAlchemySimilarityResultsRepository('sqlite:///tagging.db')
service = MediaSimilarityService(repository)

request = MediaClusteringRequest(
  media_paths=[
    'image1.png',
    'image2.png',
    'image3.png',
    ],
    media_type='IMAGE',
    tagger_type='gemini',
)

clusters = service.cluster_media(request)
```
///

## Using dedicated databases

You can use two different databases for tagging and similarity results.

/// tab | cli
```bash
media-similarity cluster image1.png image2.png image3.png \
  --media-type IMAGE \
  --tagger gemini \
  --db-uri sqlite:///similarity.db \
  --tagging.db_uri=sqlite:///tagging.db
```
///

/// tab | python
```python
import media_tagging
from media_similarity import MediaClusteringRequest, MediaSimilarityService

from media_tagging.repositories import SqlAlchemyTaggingResultsRepository
from media_similarity.repositories import SqlAlchemySimilarityResultsRepository

tagging_repository = SqlAlchemyTaggingResultsRepository('sqlite:///tagging.db')

tagging_service = media_tagging.MediaTaggingService(tagging_repository)
repository = SqlAlchemySimilarityResultsRepository('sqlite:///similarity.db')

service = MediaSimilarityService(
  media_similarity_repository=repository,
  tagging_service=tagging_service)

request = MediaClusteringRequest(
  media_paths=[
    'image1.png',
    'image2.png',
    'image3.png',
    ],
    media_type='IMAGE',
    tagger_type='gemini',
)

clusters = service.cluster_media(request)
```
///
