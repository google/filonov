# Tagging media with Gemini

## Prerequisites

- A GCP project with billing account attached
- [Vertex AI API](https://pantheon.corp.google.com/apis/library/aiplatform.googleapis.com) enabled.
- [GOOGLE_API_KEY](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Google Gemini.
- `GOOGLE_CLOUD_PROJECT` - points the Google Cloud project with Vertex AI API enabled.

```bash
export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
export GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_HERE>
```

## Installation

/// tab | pip
```python
pip install media-tagging
```
///

/// tab | uv
```python
uv pip install media-tagging
```
///


## Usage


/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini
```
///

/// tab | python
```python
import media_tagging

media_tagger = media_tagging.MediaTaggingService()

result = media_tagger.tag_media(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
)

result.save(output='tagging_results', writer='csv')
```

## Tagger customizations

### Video

For `VIDEO` and `YOUTUBE_VIDEO` media types you can specify video specific parameters (`fps`, `start_offset`, `end_offset`)

/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.fps=5 \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python
import media_tagging

media_tagger = media_tagging.MediaTaggingService()

result = media_tagger.tag_media(
  media_type='VIDEO',
  media_paths=['video1.mp4', 'video2.mp4'],
  tagger_type='gemini',
  tagging_options={
    'fps': 5,
  },
)

result.save(output='tagging_results', writer='csv')
```
///
