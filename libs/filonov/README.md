# Filonov library & CLI tool

[![PyPI](https://img.shields.io/pypi/v/filonov?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/filonov)

## Prerequisites

- Python 3.10+
- [Prerequisites](../media_tagging/README.md#prerequisites) for `media-tagging` library satisfied

## Installation

```
pip install filonov
```
> Install filonov with UI support to have a visual way of file generation `pip install filonov[ui]`

## Usage

Run `filonov` based on one of the following sources:
> Alternatively run `filonov-ui` to generate files in an interactive UI.

`filonov` supports three main modes determined by the `--source` argument:

* `googleads` - fetch all assets from a Google Ads account / MCC.
* `file` - fetch all assets with their tags and metrics from CSV files
* `youtube` - fetch public videos from a YouTube channel.


### Google Ads API
```
filonov --source googleads --media-type <MEDIA_TYPE> \
  --db-uri=<CONNECTION_STRING> \
  --tagger=<TAGGER_TYPE> \
  --googleads.ads_config_path=<PATH-TO-GOOGLE-ADS-YAML> \
  --googleads.campaign-types=<CAMPAIGN_TYPE> \
  --googleads.account=<ACCOUNT_ID> \
  --googleads.start-date=YYYY-MM-DD \
  --googleads.end-date=YYYY-MM-DD  \
  --size-base=cost \
  --trim-tags-threshold <TAG_TRIM_THRESHOLD> \
  --parallel-threshold <N_THREADS> \
  --output-name <FILE_NAME>
```
where:

- `<MEDIA_TYPE>` - one of `IMAGE` or `YOUTUBE_VIDEO`
- `<CAMPAIGN_TYPE>` - all possible combinations `app`, `pmax`, `demandgen`, `display`, `video` separated by commas.
- `<TAGGER_TYPE>` - one of possible media taggers listed [here](../media_tagging/README.md#supported-taggers')
- `<ACCOUNT_ID>` - Google Ads Account Id in 1234567890 format. Can be MCC.
- `<CONNECTION_STRING>` - Connection string to the database with tagging results
  (i.e. `sqlite:///tagging.db`). Make sure that DB exists.
  > To create an empty Sqlite DB call `touch database.db`.
- `<PATH-TO-GOOGLE-ADS-YAML>` - path to `google-ads.yaml`.
- `<TAG_TRIM_THRESHOLD>` - Remove all tags with score lower than provided threshold.
- `<FILE_NAME>` - Path to store results of running `filonov`. By default results are stored in the same folder where `filonov` is run, but you can provide any custom path (including remote one).

**Examples**

1. Analyze all images in App campaigns for the last 30 days

```
filonov --source googleads --media-type IMAGE \
  --googleads.campaign-types=app \
  --googleads.account=<ACCOUNT_ID>
```

2. Analyze all images in DemandGen campaigns for the January 2025

```
filonov --source googleads --media-type IMAGE \
  --googleads.campaign-types=demandgen \
  --googleads.start_date=2025-01-01 \
  --googleads.end_date=2025-01-31 \
  --googleads.account=<ACCOUNT_ID>
```

3. Save results to Google Cloud Storage

```
filonov --source googleads --media-type IMAGE \
  --googleads.campaign-types=app \
  --googleads.account=<ACCOUNT_ID> \
  --output-name gs://<YOUR_BUCKET>/filonov
```

> In order to use `filonov` for tagging YOUTUBE_VIDEO in Google Ads account
> (with parameters `--source googleads --media-type YOUTUBE_VIDEO`)
> you need to be a content owner or
> request data only for publicly available videos.
> Alternatively if you have access to video files you can perform media tagging before
> running `filonov`. Check `media-tagging` [README](../media_tagging/README.md#installation)
> for more details.


### Local files

```
filonov --source file --media-type <MEDIA_TYPE> \
  --db-uri=<CONNECTION_STRING> \
  --tagger=<TAGGER_TYPE> \
  --file.path=<PATH_TO_CSV_WITH_PERFORMANCE_RESULTS> \
  --file.media_identifier=<COLUMN_WITH_MEDIA_URL> \
  --file.media_name=<COLUMN_WITH_MEDIA_NAME> \
  --file.metric_names=<COMMA_SEPARATED_METRICS_IN_FILE> \
  --size-base=cost \
  --parallel-threshold <N_THREADS> \
  --output-name <FILE_NAME>
```
where:

- `<MEDIA_TYPE>` - one of `IMAGE`, `VIDEO` or `YOUTUBE_VIDEO`
- `<TAGGER_TYPE>` - one of possible media taggers listed [here](../media_tagging/README.md')
> `tagger` can be omitted - in that case `filonov` will search any loaded tagging data in provided database.
- `<CONNECTION_STRING>` - Connection string to the database with tagging results
  (i.e. `sqlite:///tagging.db`). Make sure that DB exists.
  > To create an empty Sqlite DB call `touch database.db`.
- `<PATH_TO_CSV_WITH_PERFORMANCE_RESULTS>` - path to csv file containing performance results.
- `<COLUMN_WITH_MEDIA_URL>` - column name in the file where media urls are found (defaults to `media_url`).
- `<COLUMN_WITH_MEDIA_NAME>` - column name in the file where name of media is found (defaults to `media_name`).
- `<COMMA_SEPARATED_METRICS_IN_FILE>` - comma separated names of metrics to be injected into the output.
- `<FILE_NAME>` - Path to store results of running `filonov`. By default results are stored in the same folder where `filonov` is run, but you can provide any custom path (including remote one).

**Examples**

1. Get performance data from `performance.csv` file and search for tags in provided DB.

```
filonov --source file --media-type IMAGE \
  --file.path=performance.csv \
  --db-uri sqlite:///tagging.db
```

2. Get performance data from `performance.csv` file and perform tagging with `gemini` tagger.

```
filonov --source file --media-type IMAGE \
  --file.path=performance.csv \
  --tagger gemini
```

### YouTube Channel

```
filonov --source youtube \
  --db-uri=<CONNECTION_STRING> \
  --youtube.channel=YOUR_CHANNEL_ID \
  --parallel-threshold 10 \
  --output-name <FILE_NAME>
```
