# Getting data from Display & Video 360 (Bid Manager)

You can get video performance data from various campaigns in Display & Video 360 via Bid Manager API.

## Prerequisites

* [Bid Manager API](https://console.cloud.google.com/apis/library/doubleclickbidmanager.googleapis.com) enabled.
* [Credentials](https://developers.google.com/bid-manager/guides/get-started/generate-credentials) configured, can be exposed  as `GARF_BID_MANAGER_CREDENTIALS_FILE` ENV variable

## Usage

/// tab | cli
```bash
media-fetcher \
  --source dbm \
  --dbm.advertiser=ACCOUNT_ID
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import dbm

fetcher = media_fetching.MediaFetchingService(source='dbm')
request = dbm.BidManagerFetchingParameters(
  advertiser='ADVERTISER_ID',
)
report = fetcher.fetch(request)
```

> Reports can be written and processed. Learn more at [garf](https://google.github.io/garf/).
///


## Parameters

###  Mandatory

* `advertiser` - Advertiser to get data from.

###  Optional

* `ads-config` - Path to `google-ads.yaml` file. If not provided then:
    * Environmental variable `GOOGLE_ADS_CONFIGURATION_FILE_PATH`
    * Searched `$HOME` directory as `google-ads.yaml`.
* `line_item_type` - Type of line item.
* `country` - One or many countries.
* `start-date` - First date of the period in `YYYY-MM-DD` format (i.e. `2025-01-01`). Defaults to 30 days ago.
* `end-date` - Last date of the period in `YYYY-MM-DD` format. Defaults to yesterday.


/// tab | cli
```bash
media-fetcher \
  --source dbm \
  --media-type YOUTUBE_VIDEO \
  --dbm.advertiser=ADVERTISER_ID \
  --dbm.line-item-type='Demand Gen' \
  --dbm.start-date=2025-01-01 \
  --dbm.end-date=2025-01-31 \
  --dbm.country="United States"
```
///

/// tab | python

```python
import media_fetching
from media_fetching.sources import dbm

fetcher = media_fetching.MediaFetchingService(source='dbm')
request = dbm.BidManagerFetchingParameters(
  advertiser='ADVERTISER_ID',
  line_item_type='Demand Gen',
  start_date='2025-01-01',
  end_date='2025-01-31',
  country='United States'
)
report = fetcher.fetch(request)
```
///
