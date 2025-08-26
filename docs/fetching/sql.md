
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

* [Postgres](https://docs.sqlalchemy.org/en/20/core/engines.html#postgresql)
* [MySQL](https://docs.sqlalchemy.org/en/20/core/engines.html#mysql)
* [External](https://docs.sqlalchemy.org/en/20/dialects/index.html)

## Usage

/// tab | cli
```bash
media-fetcher \
  --source sqldb \
  --sqldb.connection_string=sqlite:///media_results.db \
  --sqldb.table=table_name
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

* `connection_string` - Database URL in [SQLAlchemy format](https://docs.sqlalchemy.org/en/20/core/engines.html).
* `table` - Name of a table in the database.

### Optional

* `media_identifier` - column name in the table representing path to the media.
* `media_name` - column name in the table representing name of the media.
* `metrics` - column names of metrics to get from the table.
* `segments` - column names of dimensions to get from the table.


/// tab | cli
```bash
media-fetcher \
  --source sqldb \
  --sqldb.connection-string=sqlite:///media_results.db \
  --sqldb.table=table_name \
  --sqldb.media-identifier=media_url \
  --sqldb.media-name=media_name \
  --sqldb.metrics=clicks,impressions \
  --sqldb.segments=date
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
  media_identifier='media_url',
  media_name='media_name',
  metrics=['clicks', 'impressions'],
  segments=['date'],

)
report = fetcher.fetch(request)
```
///
