# Media Tagger

## Problem statement

When analyzing large amount of creatives of any nature (being images and videos)
it might be challenging to quickly and reliably understand their content
and gain insights.

## Solution

`media-tagger` performs tagging of image and videos based on various taggers
- simply provide a path to your media files and `media-tagger` will do the rest.

## Deliverable (implementation)

`media-tagger` is implemented as a:

* **library** - Use it in your projects with a help of `media_tagging.tagger.create_tagger` function.
* **CLI tool** - `media-tagger` tool is available to be used in the terminal.
* **HTTP endpoint** - `media-tagger` can be easily exposed as HTTP endpoint.
* **Langchain tool**  - integrated `media-tagger` into your Langchain applications.

## Deployment

### Prerequisites

- Python 3.11+
- A GCP project with billing account attached
- [Video Intelligence API](https://console.cloud.google.com/apis/library/videointelligence.googleapis.com) and [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) enabled.
* [API key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Google Gemini.
  - Once you created API key export it as an environmental variable

    ```
    export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
    ```


### Installation

Install `media-tagger` with `pip install media-tagging[all]` command.

Alternatively you can install subsets of `media-tagging` library:

* `media-tagging[api]` - tagging videos and images with Google Cloud APIs.
    *  `media-tagging[image-api]` - only for tagging images.
    *  `media-tagging[video-api]` - only for tagging videos.
* `media-tagging[llm]` - tagging videos and images with LLMs.
    *  `media-tagging[base-llm]` - only for tagging images with llms.
    *  `media-tagging[google-genai]` - only for tagging images via Gemini.
    *  `media-tagging[google-vertexai]` - only for tagging videos via Gemini.

### Usage

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
* `MEDIA_PATHs` - names of files for tagging (can be urls).
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

> `langchain` and `gemini` taggers can use `custom-prompt` parameter to adjust built-in prompts.
