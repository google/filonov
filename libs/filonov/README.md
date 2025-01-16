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


* Google Ads API
```
filonov --source googleads --media-type <MEDIA_TYPE> \
  --campaign-type <CAMPAIGN_TYPE> \
  --db-uri=<CONNECTION_STRING> \
  --googleads.tagger=<TAGGER_TYPE> \
  --googleads.ads_config_path=<PATH-TO-GOOGLE-ADS-YAML> \
  --googleads.account=<ACCOUNT_ID> \
  --googleads.start-date=YYYY-MM-DD \
  --googleads.end-date=YYYY-MM-DD  \
  --size-base=cost \
  --parallel-threshold <N_THREADS>
```
where:

- `<MEDIA_TYPE>` - one of `IMAGE` or `YOUBE_VIDEO`
- `<CAMPAIGN_TYPE>` - one of `app`, `pmax`, `demandgen`, `display`, `video`
- `<TAGGER_TYPE>` - one of possible media taggers listed [here](../media_tagging/README.md')
- `<ACCOUNT_ID>` - Google Ads Account Id in 1234567890 format. Can be MCC.
- `<CONNECTION_STRING>` - Connection string to the database with tagging results
  (i.e. `sqlite:///tagging.db`). Make sure that DB exists.
  > To create an empty Sqlite DB call `touch database.db`.
- `<PATH-TO-GOOGLE-ADS-YAML>` - path to `google-ads.yaml`.

* Local files

```
filonov --source file --media-type YOUTUBE_VIDEO \
  --db-uri=<CONNECTION_STRING> \
  --file.tagging_results_path=<PATH_TO_CSV_WITH_TAGGING_RESULTS> \
  --file.performance_results_path=<PATH_TO_CSV_WITH_PERFORMANCE_RESULTS> \
  --size-base=cost \
  --parallel-threshold <N_THREADS>
```

   File with performance results should contains the following columns:

   - media_url
   - media_name

   File with tagging results should contains the following columns:
   - media_url
   - tag
   - score

* All public video in YouTube channel

```
filonov --source youtube --media-type YOUTUBE_VIDEO \
  --db-uri=<CONNECTION_STRING> \
  --youtube.channel=YOUR_CHANNEL_ID \
  --parallel-threshold 10
```
