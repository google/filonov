# Processing with Gemini

## Prerequisites

- A GCP project with billing account attached
- [GOOGLE_API_key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Google Gemini.
- `GOOGLE_CLOUD_PROJECT` - points the Google Cloud project with Vertex AI API enabled.

```bash
export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
export GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_HERE>
```

## Installation

/// tab | pip
```python
pip install filonov
```
///

/// tab | uv
```python
uv pip install filonov
```
///


## Usage


```bash
media-tagger ACTION MEDIA_PATHs \
  --media-type <MEDIA_TYPE> \
  --tagger <TAGGER_TYPE> \
  --db-uri=<CONNECTION_STRING> \
  --writer <WRITER_TYPE> \
  --output <OUTPUT_FILE_NAME>
```

where:

* `ACTION` - either `tag` or `describe`.
* `MEDIA_PATHs` - names of files for tagging (can be urls) separated by spaces.
> Instead of reading `MEDIA_PATHs` as positional arguments you can read them
> from  a file using
> `--input FILENAME.CSV` argument.
> Use `--input.column_name=NAME_OF_COLUMN` to specify column name in the file.
* `<MEDIA_TYPE>` - type of media (YOUTUBE_VIDEO, VIDEO, IMAGE, TEXT).
* `<TAGGER_TYPE>` - name of tagger, [supported options](#supported-taggers).
> Tagger can be customized via `tagger.option=value` syntax. I.e. if you want to request a specific number of tags you can add `--tagger.n-tags=100` CLI flag.
* `<CONNECTION_STRING>` - Optional connection string to the database with tagging results (i.e. `sqlite:///tagging.db`). If this parameter is set make sure that DB exists.
> To create an empty Sqlite DB execute `touch database.db`.
* `<WRITER_TYPE>` - writer identifier (check available options at [garf-io library](https://github.com/google/garf/tree/main/libs/garf_io#readme)).
* `<OUTPUT_FILE_NAME>` - name of the file to store results of tagging (by default `tagging_results`).

## Tagger customizations

* `langchain` and `gemini` taggers can use `custom-prompt` parameter to adjust built-in prompts.
Add `--tagger.custom-prompt=YOUR_PROMPT_HERE`, where YOUR_PROMPT_HERE is either prompt or a file path (local or remote) with `.txt` extension.

     > Example: `--tagger.custom_prompt="Is this an advertising? Answer yes or no'`
     * When passing custom prompt you can opt out of using built in schemas in `media-tagger` by using `--tagger.no-schema=True` or provide a [custom schema](https://ai.google.dev/gemini-api/docs/structured-output#json-schemas) via `--tagger.custom_schema=/path/to/schema.json` parameter.
* `gemini` tagger for `video` and `youtube_video` media types supports specifying `VideoMetadata` parameters (`fps`, `start_offset`, `end_offset`)
     > Example: `--tagger.fps=5`
* `gemini` tagger can use `n_runs=N` parameter to repeat tagging process `N` times, i.e. `--tagger.n_runs=10` will tag the same medium 10 times.
