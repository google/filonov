## Installation

Fetching from BigQuery requires installing extra dependency.

/// tab | pip
```bash
pip install media-fetching[bq]
```
///

/// tab | uv
```bash
uv pip install media-fetching[bq]
```
///

## Usage

/// tab | cli
```bash
media-fetcher \
  --source bq \
  --bq.table=project.dataset.table
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import sql

fetcher = media_fetching.MediaFetchingService(source='bq')
request = sql.BigQueryFetchingParameters(
  table='project.dataset.table'
)
report = fetcher.fetch(request)
```

> Reports can be written and processed. Learn more at [garf](https://google.github.io/garf/).
///



## Parameters

###  Mandatory

* `table` - Fully qualified name of the table in BigQuery (in `project.dataset.table` format).

### Optional

* `media_identifier` - column name in the table representing path to the media.
* `media_name` - column name in the table representing name of the media.
* `metrics` - column names of metrics to get from the table.
* `segments` - column names of dimensions to get from the table.

/// tab | cli
```bash
media-fetcher \
  --source bq \
  --bq.table=project.dataset.table \
  --bq.media-identifier=media_url \
  --bq.media-name=media_name \
  --bq.metrics=clicks,impressions \
  --bq.segments=date
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import sql

fetcher = media_fetching.MediaFetchingService(source='bq')
request = sql.BigQueryFetchingParameters(
  table='project.dataset.table',
  media_identifier='media_url',
  media_name='media_name',
  metrics=['clicks', 'impressions'],
  segments=['date'],

)
report = fetcher.fetch(request)
```
///
