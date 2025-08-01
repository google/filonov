Fetching from a file expects either local or remote CSV.


## Usage

/// tab | cli
```bash
media-fetcher \
  --source file \
  --file.path=PATH_TO_FILE.csv \
  --media-type IMAGE
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

###  Optional

* media_identifier=IDENTIFIER_OF_MEDIA
* metric_names=COMMA_SEPARATED_METRIC_NAMES
