`media-similarity` finds how similar media are and combines them into clusters.

Similarity is calculated based on tags provided by [`media-tagging`](../tagging/overview.md) library and takes into
account how many similar tags two media have.

## Key features

* Clusters media into groups of similar media.
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

`cluster` commands writes data to local / remote storage via [garf-io](https://google.github.io/garf/usage/writers/) with the following columns:

* `cluster_id` - id of a cluster medium belongs.
* `media_url` - identifier of medium.
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

`cluster_media` returns `ClusteringResults` object which contains the following properties:

* `clusters` - mapping between medium and its assigned cluster id.
* `adaptive_threshold` - threshold used to identify whether two media belong to the same cluster.
* `graph_info` -  stores information on each medium and its relationship to other media.


`ClusteringResults` can be written to local / remote storage via [garf-io](https://google.github.io/garf/usage/writers/) with `to_garf_report` method with the following columns:

* `cluster_id` - id of a cluster medium belongs.
* `media_url` - identifier of medium.
///

### Similarity Search

`media-similarity` can search for similar media given a set of seed media.

> Please note that this requires [persistence setup](persistence.md).



/// tab | cli
```
media-similarity search image1 image2 \
  --media-type IMAGE \
  --db-uri=<CONNECTION_STRING>
```

`search` commands writes data to local / remote storage via [garf-io](https://google.github.io/garf/usage/writers/) with the following columns:

* `seed_media_identifier` - identifier of media used to perform a search.
* `media_identifier` - identifier of found similar media.
* `score` - similarity score showing how strong the connection between two media.
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

`find_similar_media` returns list of `SimilaritySearchResults` objects each containing the following properties:

* `seed_media_identifier` - identifier of media used to perform a search.
* `results` - identifiers of the most similar media with their similarity scores.


`SimilaritySearchResults` can be written to local / remote storage via [garf-io](https://google.github.io/garf/usage/writers/) with `to_garf_report` method with the following columns:

* `cluster_id` - id of a cluster medium belongs.
* `media_url` - identifier of medium.
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

`compare` commands writes data to local / remote storage via [garf-io](https://google.github.io/garf/usage/writers/) with the following columns:

* `media_pair_identifier` - identifier of a media pair (pipe separated media ids of two media).
* `score` - similarity score for media pair.
* `similar_tags` - number of common tags between media.
* `similarity_weight_normalized` - weight of similar tags normalized by inverse-document frequency.
* `similarity_weight_unnormalized` - weight of similar tags.
* `dissimilar_tags`- number of dissimilar tags between media.
* `dissimilarity_weight_normalized` - weight of dissimilar tags normalized by inverse-document frequency.
* `dissimilarity_weight_unnormalized` - weight of dissimilar tags.
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

`compare_media` returns list of `MediaSimilarityComparisonResult` objects each containing the following properties:

* `media_pair_identifier` - identifier of a media pair (pipe separated media ids of two media).
* `similarity_score` - contains information on number of similar / dissimilar tags and their weights.


`MediaSimilarityComparisonResult` can be written to local / remote storage via [garf-io](https://google.github.io/garf/usage/writers/) with `to_garf_report` method with the following columns:

* `media_pair_identifier` - identifier of a media pair (pipe separated media ids of two media).
* `score` - similarity score for media pair.
* `similar_tags` - number of common tags between media.
* `similarity_weight_normalized` - weight of similar tags normalized by inverse-document frequency.
* `similarity_weight_unnormalized` - weight of similar tags.
* `dissimilar_tags`- number of dissimilar tags between media.
* `dissimilarity_weight_normalized` - weight of dissimilar tags normalized by inverse-document frequency.
* `dissimilarity_weight_unnormalized` - weight of dissimilar tags.
///
