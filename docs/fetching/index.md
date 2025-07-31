`media-fetcher` performs fetching of images and videos performance from various data sources.

### Installation

```
pip install media-fetching
```

### Prerequisites

- Python 3.10+
- Google Ads API [enabled and configured](https://github.com/google/ads-api-report-fetcher/blob/main/docs/how-to-authenticate-ads-api.md)
- YouTube Data API [enabled and configured](https://github.com/google/garf/tree/main/libs/garf_community/google/youtube/youtube-data-api#prerequisites)
- (Optional) If using `tagging` modules - media-tagger [configured](https://github.com/google/filonov/tree/main/libs/media_tagging#prerequisites)

### Usage

#### Fetching media

Once `media-fetcher` is installed you can call it:

```bash
media-fetcher \
  --source <MEDIA_SOURCE> \
  --media-type <MEDIA_TYPE> \
  --extra_info <EXTRA_INFO_MODULES> \
  --writer <WRITER_TYPE> \
  --output <OUTPUT_FILE_NAME>
```
where:

* `<SOURCE>` - source of media data:
    * `googleads` - fetch all assets from a Google Ads account / MCC.
    * `file` - fetch all assets with their tags and metrics from CSV files
    * `youtube` - fetch public videos from a YouTube channel.
* `<MEDIA_TYPE>` - type of media (YOUTUBE_VIDEO, VIDEO, IMAGE).
* `<WRITER_TYPE>` - writer identifier (check available options at [garf-io library](https://github.com/google/garf/tree/main/libs/garf_io#readme)).
* `<OUTPUT_FILE_NAME>` - name of the file to store results of tagging (by default `media_results`).

#### Source customizations

Source customizations are performed via `--source.parameters=value` syntax (i.e. `--googleads.account=1`)


* `googleads`:

  Mandatory:

  * account=ACCOUNT_ID

  Optional:

  * ads_config_path=PATH-TO-GOOGLE-ADS-YAML
  * campaign-types=CAMPAIGN_TYPE
  * start-date=YYYY-MM-DD
  * end-date=YYYY-MM-DD

* `youtube`:

  Mandatory:
  * channel=YOUTUBE_CHANNEL_ID

* `file`:

  Mandatory:
  * path=PATH_TO_FILE

  Optional:
  * media_identifier=IDENTIFIER_OF_MEDIA
  * metric_names=COMMA_SEPARATED_METRIC_NAMES

* `bq`:

  Mandatory:
  * table=FULLY_QUALIFIED_TABLE_NAME (in `project.dataset.table` format)

  Optional:
  * media_identifier=IDENTIFIER_OF_MEDIA
  * metric_names=COMMA_SEPARATED_METRIC_NAMES

* `sqldb`:

  Mandatory:
  * connection_string=DATABASE_CONNECTION_STRING (in [SQLAlchemy format](https://docs.sqlalchemy.org/en/14/core/engines.html))
  * table=TABLE_NAME

  Optional:
  * media_identifier=IDENTIFIER_OF_MEDIA
  * metric_names=COMMA_SEPARATED_METRIC_NAMES

#### Available extra info modules

Source customizations are performed via `--extra-info module.method` syntax (i.e. `--extra-info tagging.languages,googleads.main_geo`)

Currently supported modules:

* `googleads`:
  * main_geo - identifies main spending country for a media.
  * approval_rate - calculates approval rate (from 0 to 1) for each media.

* `tagging`:
  * language - identifies language of a media.

* `youtube`:
  * language - identifies language of YouTube Video based on YouTube Data API.
