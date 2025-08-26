Fetching from a file expects either local or remote CSV.


## Usage

/// tab | cli
```bash
media-fetcher \
  --source file \
  --file.path=PATH_TO_FILE.csv
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import file

fetcher = media_fetching.MediaFetchingService(source='file')
request = file.FileFetchingParameters(path='PATH_TO_FILE.csv')
report = fetcher.fetch(request)
```
///

## Parameters

###  Mandatory

* path=PATH_TO_FILE
* `path` - Path to local or remote CSV file..

###  Optional

* `media_identifier` - column name in the table representing path to the media.
* `media_name` - column name in the table representing name of the media.
* `metrics` - column names of metrics to get from the table.
* `segments` - column names of dimensions to get from the table.

/// tab | cli
```bash
media-fetcher \
  --source file \
  --file.path=PATH_TO_FILE.csv \
  --file.media-identifier=media_url \
  --file.media-name=media_name \
  --file.metrics=clicks,impressions \
  --file.segments=date
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import file

fetcher = media_fetching.MediaFetchingService(source='file')
request = file.FileFetchingParameters(
  path='PATH_TO_FILE.csv',
  media_identifier='media_url',
  media_name='media_name',
  metrics=['clicks', 'impressions'],
  segments=['date'],

)
report = fetcher.fetch(request)
```
///
