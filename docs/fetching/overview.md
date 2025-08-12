`media-fetcher` performs fetching of [supported media](../tagging/media.md) from various sources.

It gives you information on a single media coupled with its performance.

## Supported sources

* [googleads](googleads.md) - fetch media performance metrics from a Google Ads account / MCC.
* [youtube](youtube.md) - fetch public videos from a YouTube channel.
* [file](file.md) - load media performance metrics from CSV files
* [bq](bq.md) - load media performance metrics from BigQuery table.
* [sql](sql.md) - load media performance metrics from SqlAlchemy supported DB.

### Installation

/// tab | pip
```
pip install media-fetching
```
///

/// tab | uv
```
uv add media-fetching
```
///

### Usage

Once `media-fetcher` is installed you can call it:

```bash
media-fetcher \
  --source <MEDIA_SOURCE> \
  --media-type <MEDIA_TYPE> \
  --writer <WRITER_TYPE> \
  --output <OUTPUT_FILE_NAME>
```
where:

* `<SOURCE>` - source of media data, one of [supported sources](#supported-sources).
* `<MEDIA_TYPE>` - type of media, one of [supported media](../tagging/media.md).
* `<WRITER_TYPE>` - writer identifier (check available options at [garf-io library](https://google.github.com/garf/usage/writers)).
* `<OUTPUT_FILE_NAME>` - where to store the fetched data (by default `media_results`).
