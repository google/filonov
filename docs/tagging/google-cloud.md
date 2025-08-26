# Tagging media with Google Cloud APIs

## Prerequisites

- A GCP project with billing account attached
- [Video Intelligence API](https://console.cloud.google.com/apis/library/videointelligence.googleapis.com) and [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) enabled.

## Installation

/// tab | pip
```python
pip install media-tagging[google-cloud]
```
///

/// tab | uv
```python
uv pip install media-tagging[google-cloud]
```
///


## Usage

`google-cloud` tagger only supports `tag` command.

/// tab | cli

```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger google-cloud
```
///

/// tab | python
```python
import media_tagging

media_tagger = media_tagging.MediaTaggingService()

result = media_tagger.tag_media(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='google-cloud',
)

result.save(output='tagging_results', writer='csv')
```
///

### n_tags

`google-cloud` tag support `n_tags` parameter to limit number of tags returned from API.
Learn [more](tagging.md/#n_tags).
