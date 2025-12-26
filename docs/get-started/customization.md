`filonov` customizations can be done from multiple angles - starting from
where to get data from and ending with where to store the results.

This section explains in detail how to get the most of `filonov` built-in capabilities.

## Mandatory Parameters


Here's the full command

```bash
filonov --source SOURCE \
  --media-type MEDIA_TYPE \
  --tagger TAGGER_TYPE \
  --db-uri=CONNECTION_STRING \
  --SOURCE.PARAM=VALUE \ # setup source
  --tagger.PARAM=VALUE \ # setup tagger
  --output map|tables
```
### Source

`source` is used to specify where media performance data can be found.

Select `source` from one of the following options:

* [googleads](../fetching/googleads.md) - fetch media performance metrics from a Google Ads account / MCC.
* [youtube](../fetching/youtube.md) - fetch public videos from a YouTube channel.
* [dbm](../fetching/bid-manager.md) - load YouTube performance metrics from Display & Video 360.
* [file](../fetching/file.md) - load media performance metrics from CSV files

!!!important
    For the full list of available sources check [supported sources](../fetching/overview.md#supported-sources) section.


`source` can be customized with `--SOURCE.PARAM=VALUE` syntax for CLI or `source_parameters` dictionary in `filonov` library.

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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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

### Media Type

`media-type` is used to specify what type of media to get from the `source`.

Select `media-type` from one of the following options:

* IMAGE
* VIDEO
* TEXT
* YOUTUBE_VIDEO
* WEBPAGE

As an example we can get images from YouTube videos when fetching data from `googleads` source.

/// tab | cli
```bash hl_lines="2"
filonov --source googleads \
  --media-type YOUTUBE_VIDEO \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID
```
///

/// tab | python

```python hl_lines="7"
import filonov

service = filonov.FilonovService()

request = filonov.GenerateCreativeMapRequest(
  source='googleads',
  media_type='YOUTUBE_VIDEO',
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
```bash  hl_lines="6"
curl -X 'POST' \
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "YOUTUBE_VIDEO",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID",
    "campaign_types": "demandgen"
  }
}'
```
///

To learn more about supported media please refer to [media](../tagging/media.md) section.

### Tagger

`tagger` is used to specify how to tag data extracted from the `source`.

Select `tagger` from one of the following options:

* [gemini](../tagging/gemini.md)
* [google-cloud](../tagging/google-cloud.md)
* [langchain](../tagging/langchain.md)

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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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


## Optional Parameters

`filonov` comes with a reasonable set of defaults you can rely on.

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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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

!!!note
    You can specify different databases for `tagging` and `similarity` if needed:

    /// tab |cli
    ```bash
    filonov --source googleads --media-type IMAGE \
      --tagger gemini \
      --tagger.db-uri=CONNECTION_STRING_TO_DB_1 \
      --similarity.db-uri=CONNECTION_STRING_TO_DB_2 \
      --googleads.account=GOOGLE_ADS_ACCOUNT_ID
    ```
    ///

    /// tab | python
    ```python
    import filonov
    import media_tagging
    import media_similarity
    from media_tagging.repositories import SqlAlchemyTaggingResultsRepository
    from media_similarity.repositories import SqlAlchemySimilarityPairsRepository

    media_tagging_repository = SqlAlchemyTaggingResultsRepository(
      CONNECTION_STRING_TO_DB_1
    )
    media_tagging_service = media_tagging.MediaTaggingService(
      media_tagging_repository
    )
    similarity_service = media_similarity.MediaSimilarityService(
      media_similarity_repository=SqlAlchemySimilarityPairsRepository(
      CONNECTION_STRING_TO_DB_2
      ),
      tagging_service=media_tagging_service
    )

    service = filonov.FilonovService(
      tagging_service=media_tagging_service,
      similarity_service=media_similarity_service,
      )
    ```
    ///

    /// tab | curl
    ```bash
    curl -X 'POST' \
      'http://127.0.0.1:8000/filonov/creative_map/googleads' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "media_type": "IMAGE",
      "tagger": "gemini",
      "source_parameters": {
        "account": "GOOGLE_ADS_ACCOUNT_ID"
      },
      tagger_parameters={"db-uri": CONNECTION_STRING_TO_DB_1},
      similarity_parameters={"db-uri": CONNECTION_STRING_TO_DB_2}

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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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

You can save `filonov` results to JSON file (`creative_map.json`) that contains all necessary information to visualize the results at [http://filonov-ai.web.app](http://filonov-ai.web.app) or to a set of tables that can be used independently.

#### Creative Map

You can overwrite default location where creative map is saved with `output-name` option.


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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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

##### Preview embedding

If media type support previews (i.e. YOUTUBE_VIDEO) generated
`creative_map.json` file will contain links to previews to be downloaded
while map is rendering.

You can include previews directly into the map with `emded-previews` option so
they will be rendered instantly.


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

request = filonov.GenerateCreativeMapRequest(
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
  'http://127.0.0.1:8000/filonov/creative_map/googleads' \
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

!!! important
    Embedding previews might significantly increase map size!

#### Tables

Saving filonov results as tables allows you to use them for your own analysis without relying on [http://filonov-ai.web.app](http://filonov-ai.web.app) dashboard.

In order to save results you need to specify `writer` option.
Check all supported writers and their configuration [here](https://google.github.io/garf/usage/writers/).

/// tab | cli
```bash hl_lines="4-5"
filonov --source googleads --media-type IMAGE \
  --tagger gemini \
  --googleads.account=GOOGLE_ADS_ACCOUNT_ID \
  --output tables --writer bq \
  --bq.project=BQ_PROJECT --bq.dataset=BQ_DATASET
```
///

/// tab | python

```python hl_lines="9-13"
import filonov

service = filonov.FilonovService()

request = filonov.GenerateTablesRequest(
  source='googleads'
  media_type='IMAGE',
  tagger='gemini',
  source_parameters={'account': 'GOOGLE_ADS_ACCOUNT_ID'},
  writer='bq',
  writer_parameters={
    'project': BQ_PROJECT,
    'dataset': BQ_DATASET,
  }
)

service.generate_tables(request)
```
///

/// tab | curl
```bash hl_lines="2 11-15"
curl -X 'POST' \
  'http://127.0.0.1:8000/filonov/tables/googleads' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "media_type": "IMAGE",
  "tagger": "gemini",
  "source_parameters": {
    "account": "GOOGLE_ADS_ACCOUNT_ID"
  },
  "writer": "bq",
  "writer_parameters": {
    "project": "BQ_PROJECT",
    "dataset": "BQ_DATASET"
  }
}'
```
///
