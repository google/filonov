# Getting data from YouTube channel

You can extract video performance data (`likes` and `views`) from publicly available video in YouTube channel.

## Prerequisites

- YouTube Data API [enabled and configured](https://github.com/google/garf/tree/main/libs/garf_community/google/youtube/youtube-data-api#prerequisites)

## Usage

/// tab | cli
```bash
media-fetcher \
  --source youtube \
  --youtube.account=CHANNEL_ID
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import youtube

fetcher = media_fetching.MediaFetchingService(source='youtube')
request = youtube.YouTubeFetchingParameters(
  channel='CHANNEL_ID',
)
report = fetcher.fetch(request)
```

> Reports can be written and processed. Learn more at [garf](https://google.github.io/garf/).
///


## Parameters

###  Mandatory

* `channel` - YouTube channel Id.
