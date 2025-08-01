# Media tagging

[![PyPI](https://img.shields.io/pypi/v/media-tagging?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging)
[![Open in Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/google/filonov/blob/main/libs/media_tagging/media_tagging_demo.ipynb)

When analyzing large amount of creatives of any nature (being images and videos)
it might be challenging to quickly and reliably understand their content
and gain insights.

`media-tagger` performs tagging of image and videos based on various taggers
- simply provide a path to your media files and `media-tagger` will do the rest.

## Key features

* Provides tags

## Prerequisites

- Python 3.10+
- A GCP project with billing account attached
- API Enabled:
    - For `google-cloud` tagger: [Video Intelligence API](https://console.cloud.google.com/apis/library/videointelligence.googleapis.com) and [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) enabled.
    - For `gemini` tagger: [Vertex AI API](https://pantheon.corp.google.com/apis/library/aiplatform.googleapis.com) enabled.
- Environmental variables specified:
    * [GOOGLE_API_key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Google Gemini.
      ```
      export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
      ```
    * `GOOGLE_CLOUD_PROJECT` - points the Google Cloud project with Vertex AI API enabled.
      ```
      export GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_HERE>
      ```

## Installation

/// tab | gemini
```bash
pip install media-tagging
```
///

/// tab | google-cloud
```bash
pip install media-tagging[google-cloud]
```
///

/// tab |  langchain
```bash
pip install media-tagging media-tagging-langchain
```
///


## Usage

/// tab | cli
```bash
media-tagger
```
///

/// tab | python
```bash
media-tagger
```
///

## Supported taggers

| identifier | supported media types | tagging output | options |
| ---------- | --------------------- | -------------- | ------ |
| `google-cloud` | `image`, `video`|  `tag` | `n-tags=10` |
| `langchain` | `image`, `video`| `tag`, `description` | `n-tags=10`, `tags=tag1,tag2,tag3` |
| `gemini` | `image`, `video`, `youtube_video`| `tag`, `description`| `n-tags=10` |
