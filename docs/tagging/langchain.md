[![PyPI](https://img.shields.io/pypi/v/media-tagging-langchain?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging-langchain)
[![Downloads PyPI](https://img.shields.io/pypi/dw/media-tagging-langchain?logo=pypi)](https://pypi.org/project/media-tagging-langchain/)
# Tagging media with Langchain

If you're working with images you can use the multimodal LLMs supported by Langchain.

## Prerequisites

* A concrete Langchain library installed and configured

## Supported media

* IMAGE


## Installation

/// tab | pip
```python
pip install media-tagging-langchain
```
///

/// tab | uv
```python
uv pip install media-tagging-langchain
```
///

If you want to use server capabilities of `media-tagger` you need to install additional dependencies:

```bash
pip install media-tagging[server]
```


## Usage


/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger langchain \
  --tagger.llm_class_name=<FULLY_QUALIFIED_CLASS_NAME>
```

Where

* `<FULLY_QUALIFIED_CLASS_NAME>` - fully path to the LLM class (i.e. `langchain_google_genai.ChatGoogleGenerativeAI`). Corresponding library should be installed before calling the `media-tagger`.
///

/// tab | python
```python
import media_tagging

media_tagger = media_tagging.MediaTaggingService()

request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='langchain',
  tagging_options={
    'llm_class_name': 'langchain_google_genai.ChatGoogleGenerativeAI',
  }
)

result = media_tagger.tag_media(request)

result.save(output='tagging_results', writer='csv')
```
///

/// tab | curl
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/tag' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "langchain",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ],
    "tagging_options": {
      "llm_class_name": "langchain_google_genai.ChatGoogleGenerativeAI"
    }
  }'
```
///
