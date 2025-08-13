`media-similarity` finds how similar media are and combines them into clusters.

Similarity is calculated based on tags provided by [`media-tagging`](../tagging/overview.md) library and takes into
account how many similar tags two media have.

## Key features

* Cluster media into similar groups.
* Finds the most similar media for a set of seed media.
* Performs detailed explanation why two media are consider similar.


## Installation


/// tab | pip 
```bash
pip install media-similarity
```
///

/// tab | uv 
```bash
uv add media-similarity
```
///

## Usage

### Clustering

`media-similarity` can take several media, tag them and combine them into clusters.

/// tab | cli
```
media-similarity cluster image1.png image2.png image3.png \
  --media-type IMAGE \
  --tagger gemini
```
///

/// tab | python

```python
from media_similarity import MediaClusteringRequest, MediaSimilarityService

service = MediaSimilarityService()

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

### Similarity Search

`media-similarity` can search for similar media given a set of seed media.

> Please note that this requires [persistence setup](persistence.md).



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

### Comparison

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
