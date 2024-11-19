# Creative Maps

1. Install

```
pip install -e .
```

2. Run in API of file mode:

* `API` mode
```
filonov --mode api --media-type IMAGE \
  --api.tagger=vision-api \
  --api.db-uri=<CONNECTION_STRING> \
  --api.ads-config=<PATH-TO-GOOGLE-ADS-YAML> \
  --api.account=<ACCOUNT_ID> \
  --api.start-date=YYYY-MM-DD \
  --api.end-date=YYYY-MM-DD  \
  --output <file|json|html> \
  --parallel-threshold <N_THREADS>
```

* `File` mode

```
filonov --mode file --media-type YOUTUBE_VIDEO \
  --file.tagging_results_path=<PATH_TO_CSV_WITH_TAGGING_RESULTS> \
  --file.performance_results_path=<PATH_TO_CSV_WITH_PERFORMANCE_RESULTS> \
  --output <file|json|html> \
  --parallel-threshold <N_THREADS>
```
