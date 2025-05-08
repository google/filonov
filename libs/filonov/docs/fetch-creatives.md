# How to fetch creatives with filonov

`filonov` comes with a `creatives-fetcher` utility which allows you to fetch creative performance from a specified `source`.

`creatives-fetcher` supports two main modes determined by the `--source` argument:

* `googleads` - fetch all assets from a Google Ads account / MCC.
* `youtube` - fetch public videos from a YouTube channel.


Example command:

```
creatives-fetcher --source <SOURCE> --media-type <MEDIA_TYPE> --writer csv
```

where:

- `<SOURCE>` - one of `youtube` or `googleads`
- `<MEDIA_TYPE>` - one of `IMAGE` or `YOUTUBE_VIDEO`
> You can optionally pass flag `--media-urls-only` to return only a file with urls of creatives.

### `googleads` fetcher

```
creatives-fetcher --source googleads --media-type <MEDIA_TYPE> \
  --googleads.ads_config_path=<PATH-TO-GOOGLE-ADS-YAML> \
  --googleads.campaign-types=<CAMPAIGN_TYPE> \
  --googleads.account=<ACCOUNT_ID> \
  --googleads.start-date=YYYY-MM-DD \
  --googleads.end-date=YYYY-MM-DD  \
  --writer csv
```

### `youtube` fetcher

```
creatives-fetcher --source youtube --media-type YOUTUBE_VIDEO \
  --youtube.channel=<YOUTUBE_CHANNEL_ID \
  --writer csv
```
