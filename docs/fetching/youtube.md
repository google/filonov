# Getting data from YouTube channel

You can extract media data (including some performance data, i.e. `likes` and `views`)
from publicly available videos in YouTube channel.

Supported types of content:

* Video file
* Video description
* Video thumbnail
* Video commentaries

## Prerequisites

- YouTube Data API [enabled and configured](https://github.com/google/garf/tree/main/libs/garf_community/google/youtube/youtube-data-api#prerequisites)

## Usage

/// tab | cli
```bash
media-fetcher \
  --source youtube \
  --youtube.channel=CHANNEL_ID
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

###  Optional

* `type` - Type of content to get from channel. One of `videos`, `thumbnails`, `descriptions`, `commentaries`.

/// tab | cli
```bash hl_lines="4"
media-fetcher \
  --source youtube \
  --youtube.channel=CHANNEL_ID \
  --youtube.type=commentaries
```
///

/// tab | python

```python hl_lines="7"
import media_fetching
from media_fetching.sources import youtube

fetcher = media_fetching.MediaFetchingService(source='youtube')
request = youtube.YouTubeFetchingParameters(
  channel='CHANNEL_ID',
  type='commentaries',
)
report = fetcher.fetch(request)
```
