`filonov` combines media fetching, tagging and similarity detection libraries
in one utility and allows you to generate creative maps files to be visualized
in [http://filonov-ai.web.app](http://filonov-ai.web.app)

You can use `filonov` in one of the following forms:

* CLI tool - use `filonov` utility in your terminal or shell scripts.
* Python library - import `filonov` library to use in your Python code.
* API endpoint - start FastAPI endpoint with `python -m filonov.entrypoints.server`

## Parameters

When generating creative map files with `filonov` you need to provide several elements:

- `source` - where media performance data can be found, check [supported sources](../fetching/overview.md#supported-sources).
- `media-type` - one of [supported media types](../tagging/media.md#supported-media-types).
- `tagger` - one of [supported taggers](../tagging/overview.md#supported-taggers)

You can check full command structure [here](#command-structure).

## Example

As a simple example we can get Google Ads images from `GOOGLE_ADS_ACCOUNT_ID` account.

/// tab | cli

```bash
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID
```
///

/// tab | python

```python
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'}
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  }
}'
```
///


This will save `creative_map.json` file to the same directory where code is run.


## Customization


`filonov` supports multiple customization options.

### Source

You can configure which data you're getting from a source.


As an example we can get images from DemandGen campaigns (instead of default App campaigns) when fetching data from `googleads` source.

/// tab | cli
```bash hl_lines="4"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID \
  --googleads.campaign-types=demandgen
```
///

/// tab | python

```python hl_lines="11"
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={
    'account': 'GOOGLE_ADS_ACCOUNT_ID',
    'campaign_types': ['demandgen'],
  }
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash  hl_lines="10"
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID",
    "campaign_types": "demandgen"
  }
}'
```
///

For the full list of customization options please refer to [sources](../fetching/overview.md#supported-sources) section.


### Tagger

You can configure how to tag data extracted from the source.

As an example we can get 50 tags (instead of default 100) when performing tagging via `gemini`.

/// tab | cli
```bash hl_lines="3"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --tagger.n-tags=50 \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID
```
///

/// tab | python

```python hl_lines="9"
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  tagger_parameters={'n_tags': 50},
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'}
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash hl_lines="8-10"
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "tagger_parameters": {
    "n_tags": 50
  },
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  }
}'
```
///

For the full list of customization options please refer to [taggers](../tagging/overview.md#supported-taggers) section.


### Similarity

You can fine-tune how similarity is calculated.


/// tab | cli
```bash hl_lines="3"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --similarity.custom-threshold=2 \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID
```
///

/// tab | python

```python hl_lines="9"
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  similarity_parameters={'custom_threshold': 2},
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'}
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash hl_lines="8-10"
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "similarity_parameters": {
    "custom_threshold": 2
  },
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  }
}'
```
///

### Persistence

You can save results of tagging / similarity calculation in a database.

/// tab | cli
```bash hl_lines="3"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --db-uri CONNECTION_STRING_TO_DB \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID
```
///

/// tab | python

```python hl_lines="2 3 5-10 12"
import filonov
import media_tagging
from media_tagging.repositories import SqlAlchemyTaggingResultsRepository

media_tagging_repository = SqlAlchemyTaggingResultsRepository(
  CONNECTION_STRING_TO_DB
)
media_tagging_service = media_tagging.MediaTaggingService(
  media_tagging_repository
)

service = filonov.FilonovService(tagging_service=media_tagging_service)

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'}
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl

Expose `MEDIA_TAGGING_DB_URL` environmental variable and restart service.
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  }
}'
```
///

### Trimming

You can exclude tags with score below certain threshold when performing similarity calculation.

/// tab | cli
```bash hl_lines="4"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID \
  --trim-tags-threshold 0.5
```
///

/// tab | python

```python hl_lines="10"
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'},
  trim_tags_threshold=0.5,
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash hl_lines="11"
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  },
  "trim_tags_threshold": 0.5
}'
```
///

### Output

By default the results are saved into `creative_map.json` file in the current folder.

You can overwrite it with `output-name` option.


Let's save map into `map1.json` file.


/// tab | cli
```bash hl_lines="4"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID \
  --output-name map1
```
///

/// tab | python

```python hl_lines="10"
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'},
  output_parameters={'output_name': 'map1'},
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash hl_lines="11-13"
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  },
  "output_parameters": {
    "output_name": "map1"
  }
}'
```
///

///

### Preview embedding

If media-type support previews (i.e. YOUTUBE_VIDEO) generated
`creative_map.json` file will contain links to previews to be downloaded
during map rendering.

You can include previews directly into the map with `emded-previews` option so
they will be rendered instantly.

!!! important
    Embedding previews might significantly increase map size!



/// tab | cli
```bash hl_lines="4"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID \
  --embed-previews
```
///

/// tab | python

```python hl_lines="10"
import filonov

service = filonov.FilonovService()

request = filonov.CreativeMapGenerateRequest(
  source='googleads',
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'},
  embed_previews=True,
)

creative_map = service.generate_creative_map(request)
creative_map.save('creative_map')

```
///

/// tab | curl
```bash hl_lines="11"
curl -X 'POST' \
  'http://127.0.0.1:8000/creative_maps/generate:googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  },
  "embed_previews": "true",
}'
```
///

## Command structure

```bash
filonov --source SOURCE \
  --media-type MEDIA_TYPE \
  --db-uri=CONNECTION_STRING \
  --tagger=TAGGER_TYPE \
  --SOURCE.PARAM=VALUE \
  --tagger.PARAM=VALUE \
  --output-name=FILE_NAME
```
