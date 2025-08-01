# Getting data from Google Ads

You can extra asset performance data from various campaigns in Google Ads.

## Prerequisites

- Google Ads API [enabled and configured](https://github.com/google/ads-api-report-fetcher/blob/main/docs/how-to-authenticate-ads-api.md)

## Usage

/// tab | cli
```bash
media-fetcher \
  --source googleads \
  --googleads.account=ACCOUNT_ID \
  --media-type IMAGE
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
  campaign_types=['demandgen', 'pmax'],
)
report = fetcher.fetch(request)
```

> Reports can be written and processed. Learn more at [garf](https://google.github.io/garf/).
///


## Parameters

###  Mandatory

* `account` - Google Ads account to get data from. Can be either MCC or child account.

###  Optional

* `ads_config_path` - Path to `google-ads.yaml` file. If not provided then:
    * Environmental variable `GOOGLE_ADS_CONFIGURATION_FILE_PATH`
    * Searched `$HOME` directory as `google-ads.yaml`.
* `campaign-types` - Type of campaigns to get data from. Choose one of the following or select option `all` to get all available media of a single media type.
    * `pmax`
    * `demandgen`
    * `search`
    * `display`
    * `app`
    * `video`
* `start-date` - First date of the period in `YYYY-MM-DD` format (i.e. `2025-01-01`). Defaults to 30 days ago.
* `end-date` - Last date of the period in `YYYY-MM-DD` format. Defaults to yesterday.
