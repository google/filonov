## Finding similar media

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

### Working with clusters

Once `cluster_media` is executed you get a `ClusteringResults` object which contains:

* `clusters` - mapping between media url and its assigned cluster
* `adaptive_threshold` - minimal value for defining similar media.
* `graph` -mapping with nodes and edges.

You can get clusters two ways:

* via `.clusters` property as a dict
* via `.to_garf_report` method as a GarfReport which contains two columns - `media_url` and `cluster_id`.
