# Available extra info modules

Source customizations are performed via `--extra-info module.method` syntax (i.e. `--extra-info tagging.languages,googleads.main_geo`)

## Prerequisites

- (Optional) If using `tagging` enricher - media-tagger [configured](../tagging/tagging.md#prerequisites)

## Supported enrichers

### googleads

* main_geo - identifies main spending country for a media.
* approval_rate - calculates approval rate (from 0 to 1) for each media.

### tagging

* language - identifies language of a media.

### youtube

* language - identifies language of YouTube Video based on YouTube Data API.

## Usage

Suppose we want to use Gemini to identify language of each media found in a file `media.csv`.

/// tab | cli
```bash
media-fetcher \
  --source file \
  --file.path=media.csv \
  --media-type IMAGE \
  --extra_info tagging.language
```
///

/// tab | python

```python
import media_fetching

fetcher = media_fetching.MediaFetchingService(source='file')
request = {'path': 'media.csv', 'extra_info': ['tagging.language']}
report = fetcher.fetch(request)
```
///
