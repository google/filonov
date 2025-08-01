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
  --bq.table=project.dataset.table \
  --media-type IMAGE
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

##  Mandatory

* `table` - Fully qualified name of the table in BigQuery (in `project.dataset.table` format).

## Optional

* media_identifier=IDENTIFIER_OF_MEDIA
* metric_names=COMMA_SEPARATED_METRIC_NAMES
