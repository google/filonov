# Available extra info modules

Source customizations are performed via `--extra-info module.method` syntax (i.e. `--extra-info tagging.languages,googleads.main_geo`)

## Prerequisites

- (Optional) If using `tagging` enricher - media-tagger must be [configured](../tagging/tagging.md#prerequisites)

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

## Supported enrichers

### googleads

* main_geo - identifies main spending country for a media.
* approval_rate - calculates approval rate (from 0 to 1) for each media.

/// tab | cli
```bash
media-fetcher \
  --source googleads \
  --googleads.account=ACCOUNT_ID \
  --media-type IMAGE \
  --extra_info googleads.main_geo,googleads.approval_rate
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import googleads

fetcher = media_fetching.MediaFetchingService(source='googleads')
request = googleads.GoogleAdsFetchingParameters(
  account='ACCOUNT_ID',
  media_type='IMAGE',
  extra_info=['googleads.main_geo', 'googleads.approval_rate'],
)

report = fetcher.fetch(request)
```
///

### tagging

* language - identifies language of a media.

/// tab | cli
```bash
media-fetcher \
  --source googleads \
  --googleads.account=ACCOUNT_ID \
  --media-type IMAGE \
  --extra_info tagging.language
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import googleads

fetcher = media_fetching.MediaFetchingService(source='googleads')
request = googleads.GoogleAdsFetchingParameters(
  account='ACCOUNT_ID',
  media_type='IMAGE',
  extra_info=['tagging.language'],
)

report = fetcher.fetch(request)
```
///

### youtube

* language - identifies language of YouTube Video based on YouTube Data API.

/// tab | cli
```bash
media-fetcher \
  --source googleads \
  --googleads.account=ACCOUNT_ID \
  --media-type YOUTUBE_VIDEO \
  --extra_info youtube.language
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import googleads

fetcher = media_fetching.MediaFetchingService(source='googleads')
request = googleads.GoogleAdsFetchingParameters(
  account='ACCOUNT_ID',
  media_type='IMAGE',
  extra_info=['youtube.language'],
)

report = fetcher.fetch(request)
```
///
