# Media Tagging with Langchain

[![PyPI](https://img.shields.io/pypi/v/media-tagging-langchain?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging-langchain)

Makes it possible to use [`media_tagging` library](https://google.github.io/filonov/tagging/overview/) with Langchain supported multimodal LLMs.

## Installation

```
pip install media-tagging-langchain
```

## Usage

> For a general purpose usage please refer to `media_tagging` [usage documentation](https://google.github.io/filonov/tagging/overview/).

```
media-tagger ACTION MEDIA_PATHs \
  --media-type <MEDIA_TYPE> \
  --tagger langchain \
  --db-uri=<CONNECTION_STRING> \
  --writer <WRITER_TYPE> \
  --output <OUTPUT_FILE_NAME>
```
where:
* `ACTION` - either `tag` or `describe`.
* `MEDIA_PATHs` - names of files for tagging (can be urls) separated by spaces.
> Instead of reading `MEDIA_PATHs` as positional arguments you can read them
> from  a file using \
> `--input FILENAME.CSV` argument.
> Use `--input.column_name=NAME_OF_COLUMN` to specify column name in the file.
* `<MEDIA_TYPE>` - type of media (IMAGE, TEXT).
* `<CONNECTION_STRING>` - Optional connection string to the database with tagging results (i.e. `sqlite:///tagging.db`). If this parameter is set make sure that DB exists.
* `<WRITER_TYPE>` - writer identifier (check available options at [garf-io library](https://google.github.io/garf/usage/writers/)).
* `<OUTPUT_FILE_NAME>` - name of the file to store results of tagging (by default `tagging_results`).

## Documentation

Explore full documentation on working with Langchain media tagging.

* [Documentation](https://google.github.io/filonov/tagging/langchain/)
