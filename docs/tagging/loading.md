If you want to import tags to be used later, you can use `media-loader` utility.



```
media-loader PATH_TO_FILE \
  --media-type <MEDIA_TYPE> \
  --loader <LOADER_TYPE> \
  --db-uri=<CONNECTION_STRING> \
  --action <ACTION>
```
where:

* `<MEDIA_TYPE>` - one of supported [media types](media.md).
> For YouTube file uploads specify YOUTUBE_VIDEO type.
* `<LOADER_TYPE>` - one of supported [loader types](#loaders).
> Loader can be customized via `loader.option=value` syntax. I.e. if you want to change the default column name with media tags are located you can specify `--loader.tag_name=new_column_name` CLI flag.
* `<CONNECTION_STRING>` - Connection string to the database with tagging results (i.e. `sqlite:///tagging.db`).
* `ACTION` - either `tag` or `describe`.

If loading tagging results with `file` loader, the CSV file should contains the following columns:

* `media_url` - location of medium (can be remote or local).
* `tag` - column that contains name of a tag.
* `score` - column that contains prominence of a tag in the media.

## Loaders

* [`file`](file-loader.md) - loads tags from a CSV file
