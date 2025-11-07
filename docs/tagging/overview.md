[![PyPI](https://img.shields.io/pypi/v/media-tagging?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging)
[![Downloads PyPI](https://img.shields.io/pypi/dw/media-tagging?logo=pypi)](https://pypi.org/project/media-tagging/)
[![Open in Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/google/filonov/blob/main/libs/media_tagging/media_tagging_demo.ipynb)

`media-tagger` performs tagging of [supported media](media.md) based on various taggers.
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

If you want to use server capabilities of `media-tagger` you need to install additional dependencies:

```bash
pip install media-tagging[server]
```


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

request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
)
result = media_tagger.tag_media(request)

result.save(output='tagging_results', writer='csv')
```
///

/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/tag' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ]
  }'
```
///

!!!note
    Instead of explicitly listing media paths you can [provide them in a file](#reading-media-from-a-file).

#### n_tags

By default `media-tagger` returns only 10 tags for the media. You can change this number with `n_tags` parameter.

/// tab | cli
```bash hl_lines="4"
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.n_tags=100 \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python hl_lines="8"
import media_tagging

media_tagger = media_tagging.MediaTaggingService()
request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={'n_tags': 100},
)

result = media_tagger.tag_media(request)

result.save(output='tagging_results', writer='csv')
```
///


/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash hl_lines="12-14"
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/tag' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ],
    "tagging_options": {
      "n_tags": 100
    }
    "
  }'
```
///

#### tags

You can use `media-tagger` to find specific tags in your media using `tags` parameter.

/// tab | cli
```bash hl_lines="4"
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.tags='cat,dog,human' \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python hl_lines="8"
import media_tagging

media_tagger = media_tagging.MediaTaggingService()
request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={'tags': ['cat', 'dog', 'human']},
)

result = media_tagger.tag_media(request)

result.save(output='tagging_results', writer='csv')
```
///

/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash hl_lines="12-14"
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/tag' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ],
    "tagging_options": {
      "tags": "cat,dog,human"
    }
    "
  }'
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

request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
)
result = media_tagger.describe_media(request)

result.save(output='description_results', writer='csv')
```
///

/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/describe' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ]
    "
  }'
```
///

!!!note
    Instead of explicitly listing media paths you can [provide them in a file](#reading-media-from-a-file).

#### custom_prompt

If you want to change the default prompt used when describing media you can specify `custom_prompt` parameter. `custom_prompt` can be either a prompt or a file path (local or remote) with `.txt` extension.

/// tab | cli
```bash hl_lines="4"
media-tagger describe MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.custom_prompt="Is this an advertising? Answer only True or False" \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python hl_lines="8-10"
import media_tagging

media_tagger = media_tagging.MediaTaggingService()
request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={
    'custom_prompt': 'Is this an advertising? Answer only True or False'
  },
)

result = media_tagger.describe_media(request)

result.save(output='tagging_results', writer='csv')
```
///

/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash hl_lines="12-14"
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/describe' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ],
    "tagging_options": {
      "custom_prompt": "Is this an advertising? Answer only True or False"
    }
    "
  }'
```
///

#### custom_schema

When passing custom prompt you can opt out of using built in schemas in `media-tagger` by using `--tagger.no-schema=True` or provide a [custom schema](https://ai.google.dev/gemini-api/docs/structured-output#json-schemas) via `custom_schema` parameter.

/// tab | cli
```bash hl_lines="4-5"
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
```python hl_lines="2 5-6 14-17"
import media_tagging
import pydantic


class CustomSchema(pydantic.BaseModel):
  answer: bool


media_tagger = media_tagging.MediaTaggingService()
request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={
    'custom_prompt': 'Is this an advertising? Answer only True or False',
    'custom_schema': CustomSchema,
  },
)

result = media_tagger.describe_media(request)

result.save(output='tagging_results', writer='csv')
```
///

/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash hl_lines="12-15"
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/describe' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ],
    "tagging_options": {
      "custom_prompt": "Is this an advertising? Answer only True or False",
      "custom_schema": "schema.json"
    }
    "
  }'
```
///


!!!example
    Here's an example schema for getting a json with a single attribute `main_theme`.
    ```json
    {
    	"type": "OBJECT",
    	"properties":  {
    		"main_theme": {
    			"type": "STRING"
    		}
    	}
    }
    ```

### Common tagger parameters

All the taggers support the following parameters.

#### n_runs

`n_runs=N` parameter to repeat tagging process `N` times.

/// tab | cli
```bash hl_lines="4"
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --tagger.n_runs=10 \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python hl_lines="8-10"
import media_tagging

media_tagger = media_tagging.MediaTaggingService()
request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
  tagging_options={
    'n_runs': 10,
  },
)

result = media_tagger.tag_media(request)

result.save(output='tagging_results', writer='csv')
```
///

/// tab | curl

> Start API by running `python -m media_tagging.entrypoints.server`.

```bash hl_lines="12-14"
curl -X 'POST' \
  'http://127.0.0.1:8000/media_tagging/tag' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "tagger_type": "gemini",
    "media_type": "IMAGE",
    "media_paths": [
      "image1.png",
      "image2.png"
    ],
    "tagging_options": {
      "n_runs": 10
    }
    "
  }'
```
///

### Reading media from a file

Instead of explicitly listing media paths you can provide them in a file.

`media-tagger` supports two types of files:

* `.txt` files - expects each media paths to be on its own line. No column names or extra columns is expected.
* `.csv` files - you can specify which column to use to read media paths.

#### Configuration

* `path` - location of the file with media paths; can be local or remote.
* `column_name`- name of the column where media_paths can be found (`media_url` by default)
* `skip_rows` - if CSV does not start with a first row, how many rows to skip (`0` by default)

/// tab | cli
```bash hl_lines="2-3"
media-tagger tag \
  --input media.csv \
  --input.column_name=url \
  --media-type IMAGE \
  --tagger gemini \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python hl_lines="2 5 9"
import media_tagging
from media_tagging import media

media_tagger = media_tagging.MediaTaggingService()
media_paths = media.get_media_paths_from_file({'path': 'media.csv'})

request = media_tagging.MediaTaggingRequest(
  media_type='IMAGE',
  media_paths=media_paths,
  tagger_type='gemini',
)
result = media_tagger.tag_media(request)

result.save(output='tagging_results', writer='csv')
```
///
/// tab | curl
**Reading media from a file currently not supported**
///
