# Filonov library & CLI tool

## Prerequisites

- Python 3.8+
- A GCP project with billing account attached
- Either [Video Intelligence API](https://console.cloud.google.com/apis/library/videointelligence.googleapis.com) or [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) enabled (depending on type of media you want to analyze).
- [Vertex AI API](https://pantheon.corp.google.com/apis/library/aiplatform.googleapis.com) enabled if you want to tag media via Vertex API AI.
- [Service account](https://cloud.google.com/iam/docs/creating-managing-service-accounts#creating) created and [service account key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating) downloaded in order to write data to interact with Vision / Video Intelligence API.

  - Once you downloaded service account key export it as an environmental variable

    ```
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/service_account.json
    ```

  - If authenticating via service account is not possible you can authenticate with the following command:
    ```
    gcloud auth application-default login
    ```

## Installation

```
pip install filonov
```

## Usage

Run `filonov` based on one of the following sources:

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
  --parallel-threshold <N_THREADS> \
  --output-name <FILE_NAME>
```
where:

- `<MEDIA_TYPE>` - one of `IMAGE` or `YOUTUBE_VIDEO`
- `<CAMPAIGN_TYPE>` - all possible combinations `app`, `pmax`, `demandgen`, `display`, `video` separated by commas.
- `<TAGGER_TYPE>` - one of possible media taggers listed [here](../media_tagging/README.md')
- `<ACCOUNT_ID>` - Google Ads Account Id in 1234567890 format. Can be MCC.
- `<CONNECTION_STRING>` - Connection string to the database with tagging results
  (i.e. `sqlite:///tagging.db`). Make sure that DB exists.
  > To create an empty Sqlite DB call `touch database.db`.
- `<PATH-TO-GOOGLE-ADS-YAML>` - path to `google-ads.yaml`.
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
filonov --source file --media-type YOUTUBE_VIDEO \
  --db-uri=<CONNECTION_STRING> \
  --file.tagging_results_path=<PATH_TO_CSV_WITH_TAGGING_RESULTS> \
  --file.performance_results_path=<PATH_TO_CSV_WITH_PERFORMANCE_RESULTS> \
  --size-base=cost \
  --parallel-threshold <N_THREADS> \
  --output-name <FILE_NAME>
```

   File with performance results should contains the following columns:

   - media_url
   - media_name

   File with tagging results should contains the following columns:
   - media_url
   - tag
   - score

### YouTube Channel

```
filonov --source youtube \
  --db-uri=<CONNECTION_STRING> \
  --youtube.channel=YOUR_CHANNEL_ID \
  --parallel-threshold 10 \
  --output-name <FILE_NAME>
```
