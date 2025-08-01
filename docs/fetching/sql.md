
## Installation

Fetching from Databases supported by SqlAlchemy requires installing extra dependency.

/// tab | pip
```bash
pip install media-fetching[sql]
```
///

/// tab | uv
```bash
uv pip install media-fetching[sql]
```
///

### Installing DB drivers

Depending on your DB you might need to install a specific DB driver for SqlAlchemy.

* Postgres
* MariaDB

## Usage

/// tab | cli
```bash
media-fetcher \
  --source sqldb \
  --sqldb.connection_string=sqlite:///media_results.db \
  --sqldb.table=table_name \
  --media-type IMAGE
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import sql

fetcher = media_fetching.MediaFetchingService(source='sqldb')
request = sql.SqlAlchemyQueryFetchingParameters(
  connection_string='sqlite:///media_results.db',
  table='table_name'
)
report = fetcher.fetch(request)
```

> Reports can be written and processed. Learn more at [garf](https://google.github.io/garf/).
///




## Parameters

###  Mandatory

* connection_string=DATABASE_CONNECTION_STRING (in [SQLAlchemy format](https://docs.sqlalchemy.org/en/14/core/engines.html))
* table=TABLE_NAME

###  Optional

* media_identifier=IDENTIFIER_OF_MEDIA
* metric_names=COMMA_SEPARATED_METRIC_NAMES
