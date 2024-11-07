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
media-tagger MEDIA_PATHs --tagger TAGGER_TYPE --writer WRITER_TYPE
```
where:
* MEDIA_PATHs - names of files for tagging (can be urls).
* TAGGER_TYPE - name of tagger, supported options:
  * `vision-api` - tags images based on [Google Cloud Vision API](https://cloud.google.com/vision/),
  * `video-api` for videos based on [Google Cloud Video Intelligence API](https://cloud.google.com/video-intelligence/)
  * `gemini-image` - Uses Gemini to tags images. Add `--tagger.n_tags=<N_TAGS>`
     parameter to control number of tags returned by tagger.
  * `gemini-structured-image`  - Uses Gemini to find certain tags in the images.
    Add `--tagger.tags='tag1, tag2, ..., tagN` parameter to find certain tags
    in the image.
  * `gemini-description-image` - Provides brief description of the image,
* WRITER_TYPE - name of writer, one of `csv`, `json`

By default script will create a single file with tagging results for each media_path.
If you want to combine results into a single file add `--output OUTPUT_NAME` flag (without extension, i.e. `--output tagging_sample`.

## Disclaimer
This is not an officially supported Google product.
