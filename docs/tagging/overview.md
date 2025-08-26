[![PyPI](https://img.shields.io/pypi/v/media-tagging?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging)
[![Open in Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/google/filonov/blob/main/libs/media_tagging/media_tagging_demo.ipynb)

`media-tagger` performs tagging of [supported media](/media.md) based on various taggers.
It generates [tagging results](tagging-result.md) which can written to local / remove storage or further processed in Python.


## Key features

* Extracts semantic tags from media.
* Describes media using custom prompt and schema.
* Saves results of tagging / description to files / databases.

## Supported taggers

* [gemini](gemini.md)
* [google-cloud](google-cloud.md)
* [langchain](langchain.md)


## Installation

`media-tagger` installation depends on which tagger you want to use.

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

`media-tagger` supports the following commands:

* tag
* describe

### Tag media

Tagging returns multiple tags for a single media. Each tag has a name and a score from 0 to 1.

/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --writer csv \
  --output tagging_results
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
///


#### n_tags

By default `media-tagger` returns only 10 tags for the media. You can change this number with `n_tags` parameter.

/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.n_tags=100 \
  --writer csv \
  --output tagging_results
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
  tagging_options={'n_tags': 100},
)

result.save(output='tagging_results', writer='csv')
```
///

#### tags

You can use `media-tagger` to find specific tags in your media using `tags` parameter.

/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.tags='cat,dog,human' \
  --writer csv \
  --output tagging_results
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
  tagging_options={'tags': ['cat', 'dog', 'human']},
)

result.save(output='tagging_results', writer='csv')
```
///

### Describe media

Description answer the question *"What this media is about?"*.

/// tab | cli
```bash
media-tagger describe MEDIA_PATHs \
  --media-type <MEDIA_TYPE> \
  --tagger <TAGGER_TYPE> \
  --writer <WRITER_TYPE> \
  --output <OUTPUT_FILE_NAME>
```
///

/// tab | python
```python
import media_tagging

media_tagger = media_tagging.MediaTaggingService()

result = media_tagger.describe_media(
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  media_type='IMAGE',
)

result.save(output='description_results', writer='csv')
```
///


#### custom_prompt

If you want to change the default prompt used when describing media you can specify `custom_prompt` parameter. `custom_prompt` can be either a prompt or a file path (local or remote) with `.txt` extension.

/// tab | cli
```bash
media-tagger describe MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.custom_prompt="Is this an advertising? Answer only True or False" \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python
import media_tagging

media_tagger = media_tagging.MediaTaggingService()

result = media_tagger.describe_media(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={
    'custom_prompt': 'Is this an advertising? Answer only True or False'
  },
)

result.save(output='tagging_results', writer='csv')
```
///

#### custom_schema

When passing custom prompt you can opt out of using built in schemas in `media-tagger` by using `--tagger.no-schema=True` or provide a [custom schema](https://ai.google.dev/gemini-api/docs/structured-output#json-schemas) via `custom_schema` parameter.

/// tab | cli
```bash
media-tagger describe MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.custom_prompt="Is this an advertising? Answer only True or False" \
  --tagger.custom_schema=./schema.json \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python
import media_tagging
import pydantic


class CustomSchema(pydantic.BaseModel):
  answer: bool


media_tagger = media_tagging.MediaTaggingService()

result = media_tagger.describe_media(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={
    'custom_prompt': 'Is this an advertising? Answer only True or False',
    'custom_schema': CustomSchema,
  },
)

result.save(output='tagging_results', writer='csv')
```
///

### Common tagger parameters

All the taggers support the following parameters.

#### n_runs

`n_runs=N` parameter to repeat tagging process `N` times.

/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.n_runs=10 \
  --writer csv \
  --output tagging_results
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
  tagging_options={
    'n_runs': 10,
  },
)

result.save(output='tagging_results', writer='csv')
```
///
