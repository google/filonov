# Creative Maps

1. Install

```
pip install -e .
```

2. Run `filonov` based on one of the following sources:

* Google Ads API
```
filonov --source googleads --media-type IMAGE \
  --db-uri=<CONNECTION_STRING> \
  --googleads.tagger=vision-api \
  --googleads.ads_config_path=<PATH-TO-GOOGLE-ADS-YAML> \
  --googleads.account=<ACCOUNT_ID> \
  --googleads.start-date=YYYY-MM-DD \
  --googleads.end-date=YYYY-MM-DD  \
  --size-base=cost \
  --parallel-threshold <N_THREADS>
```

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
   - cost
   - impressions
   - clicks
   - conversions
   - conversions_value

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
