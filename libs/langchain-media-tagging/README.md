# Langchain plugin for media-tagging library

[![PyPI](https://img.shields.io/pypi/v/media-tagging-langchain?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging-langchain)

Makes it possible to use [`media_tagging` library](https://github.com/google/filonov/blob/main/libs/media_tagging/README.md) with Langchain supported multimodal LLMs.

## Installation

```
pip install media-tagging-langchain
```

## Usage

> For a general purpose usage please refer to `media_tagging` [usage documentation](https://github.com/google/filonov/blob/main/libs/media_tagging/README.md#usage).

```
media-tagger ACTION MEDIA_PATHs \
  --media-type <MEDIA_TYPE> \
  --tagger langchain \
  --tagger.llm_class_name=<FULLY_QUALIFIED_CLASS_NAME> \
  --db-uri=<CONNECTION_STRING> \
  --writer <WRITER_TYPE> \
  --output <OUTPUT_FILE_NAME>
```
where:
* `ACTION` - either `tag` or `describe`.
* `MEDIA_PATHs` - names of files for tagging (can be urls) separated by spaces.
* `<MEDIA_TYPE>` - type of media (YOUTUBE_VIDEO, VIDEO, IMAGE).
* `<FULLY_QUALIFIED_CLASS_NAME>` - fully path to the LLM class (i.e. `langchain_google_genai.ChatGoogleGenerativeAI`). Corresponding library should be installed before calling the `media-tagger`.
* `<CONNECTION_STRING>` - Optional connection string to the database with tagging results (i.e. `sqlite:///tagging.db`). If this parameter is set make sure that DB exists.
* `<WRITER_TYPE>` - writer identifier (check available options at [garf-io library](https://github.com/google/garf/tree/main/libs/garf_io#readme)).
* `<OUTPUT_FILE_NAME>` - name of the file to store results of tagging (by default `tagging_results`).
```
