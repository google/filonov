# Tagging media with Langchain

If you're working with images you can use the multimodal LLMs supported by Langchain.

## Prerequisites

TODO

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

result = media_tagger.tag_media(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='langchain',
  tagging_options={
    'llm_class_name': 'langchain_google_genai.ChatGoogleGenerativeAI',
  }
)

result.save(output='tagging_results', writer='csv')
```
