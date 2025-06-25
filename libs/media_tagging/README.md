# Media Tagger

[![PyPI](https://img.shields.io/pypi/v/media-tagging?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/media-tagging)
[![Open in Collab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/google/filonov/blob/main/libs/media_tagging/media_tagging_demo.ipynb)

## Problem statement

When analyzing large amount of creatives of any nature (being images and videos)
it might be challenging to quickly and reliably understand their content
and gain insights.

## Solution

`media-tagger` performs tagging of image and videos based on various taggers
- simply provide a path to your media files and `media-tagger` will do the rest.

## Deliverable (implementation)

`media-tagger` is implemented as a:

* **library** - Use it in your projects with a help of `media_tagging.MediaTaggingService` class.
* **CLI tool** - `media-tagger` tool is available to be used in the terminal.
* **HTTP endpoint** - `media-tagger` can be easily exposed as HTTP endpoint.
* **Langchain tool**  - integrate `media-tagger` into your Langchain applications.

## Deployment

### Prerequisites

- Python 3.10+
- A GCP project with billing account attached
- API Enabled:
    - For `google-cloud` tagger: [Video Intelligence API](https://console.cloud.google.com/apis/library/videointelligence.googleapis.com) and [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) enabled.
    - For `gemini` tagger: [Vertex AI API](https://pantheon.corp.google.com/apis/library/aiplatform.googleapis.com) enabled.
- Environmental variables specified:
    * [GOOGLE_API_key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Google Gemini.
      ```
      export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
      ```
    * `GOOGLE_CLOUD_PROJECT` - points the Google Cloud project with Vertex AI API enabled.
      ```
      export GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_HERE>
      ```


### Installation

Install `media-tagger` with `pip install media-tagging[all]` command.

Alternatively you can install subsets of `media-tagging` library:

* `media-tagging[google-cloud]` - tagging videos and images with Google Cloud APIs.
  *  `media-tagging[google-cloud-vision]` - only for tagging images.
  *  `media-tagging[google-cloud-videointelligence]` - only for tagging videos.
* `media-tagging[gemini]` - tagging videos and images with Vertex AI API.
  *  `media-tagging[google-genai]` - only for tagging images via Gemini.
  *  `media-tagging[google-vertexai]` - only for tagging videos via Gemini.
* `media-tagging[langchain]` - tagging videos and images with Langchain.
### Usage

#### Tagging media

> This section is focused on using `media-tagger` as a CLI tool.
> Check [library](docs/how-to-use-media-tagger-as-a-library.md),
> [http endpoint](docs/how-to-use-media-tagger-as-a-http-endpoint.md),
> [langchain tool](docs/how-to-use-media-tagger-as-a-langchain-tool.md)
> sections to learn more.

Once `media-tagger` is installed you can call it:

```
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
> from  a file using \
> `--input FILENAME.CSV` argument.
> Use `--input.column_name=NAME_OF_COLUMN` to specify column name in the file.
* `<MEDIA_TYPE>` - type of media (YOUTUBE_VIDEO, VIDEO, IMAGE).
* `<TAGGER_TYPE>` - name of tagger, [supported options](#supported-taggers).
> Tagger can be customized via `tagger.option=value` syntax. I.e. if you want to request a specific number of tags you can add `--tagger.n-tags=100` CLI flag.
* `<CONNECTION_STRING>` - Optional connection string to the database with tagging results (i.e. `sqlite:///tagging.db`). If this parameter is set make sure that DB exists.
> To create an empty Sqlite DB execute `touch database.db`.
* `<WRITER_TYPE>` - writer identifier (check available options at [garf-io library](https://github.com/google/garf/tree/main/libs/garf_io#readme)).
* `<OUTPUT_FILE_NAME>` - name of the file to store results of tagging (by default `tagging_results`).

### Supported taggers

| identifier | supported media types | tagging output | options |
| ---------- | --------------------- | -------------- | ------ |
| `google-cloud` | `image`, `video`|  `tag` | `n-tags=10` |
| `langchain` | `image`, `video`| `tag`, `description` | `n-tags=10`, `tags=tag1,tag2,tag3` |
| `gemini` | `image`, `video`, `youtube_video`| `tag`, `description`| `n-tags=10` |

#### Tagger customizations

* `langchain` and `gemini` taggers can use `custom-prompt` parameter to adjust built-in prompts.\
 Add `--tagger.custom-prompt=YOUR_PROMPT_HERE`, where YOUR_PROMPT_HERE is either prompt or a file path (local or remote) with `.txt` extension.
     > Example: `--tagger.custom_prompt="Is this an advertising? Answer yes or no'`
     * When passing custom prompt you can opt out of using built in schemas in `media-tagger` by using `--tagger.no-schema=True`.
* `gemini` tagger for `video` and `youtube_video` media types supports specifying `VideoMetadata` parameters (`fps`, `start_offset`, `end_offset`)
     > Example: `--tagger.fps=5`

#### Loading tagging results

If you want to import tags to be used later, you can use `media-loader` utility.

```
media-loader PATH_TO_FILE \
  --media-type <MEDIA_TYPE> \
  --loader <LOADER_TYPE> \
  --db-uri=<CONNECTION_STRING> \
  --action <ACTION>
```
where:
* `<MEDIA_TYPE>` - type of media (YOUTUBE_VIDEO, VIDEO, IMAGE).
> For YouTube file uploads specify YOUTUBE_VIDEO type.
* `<LOADER_TYPE>` - name of loader, currently only `file` is supported (data are saved to CSV).
> Loader can be customized via `loader.option=value` syntax. I.e. if you want to change the default column name with media tags are located you can specify `--loader.tag_name=new_column_name` CLI flag.
* `<CONNECTION_STRING>` - Connection string to the database with tagging results (i.e. `sqlite:///tagging.db`). If this parameter is set make sure that DB exists.
> To create an empty Sqlite DB execute `touch database.db`.
* `ACTION` - either `tag` or `describe`.

If loading tagging results with `file` loader, the CSV file should contains the following columns:

* `media_url` - location of medium (can be remote or local).
* `tag` - column that contains name of a tag.
* `score` - column that contains prominence of a tag in the media.
