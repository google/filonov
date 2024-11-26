# Filonov - AI Creative Concept Analysis

## Problem statement

When dealing with huge amounts of creatives (video and images) it might be hard
to identify which creative approaches work the best since actual performance is
usually evaluated on a single creative.

## Solution

Filonov allows you to answer the question - what are the similarities between
my media (being image or videos). Simply links to your media, specify tagger
and get results in no time!

## Overview

Project Filonov consists of two major parts:

- Data Pipeline
- Data Visualization

Data Pipeline is currently a set of command-line tools which target is creating a JSON file
with graph of assets (images/video) grouped in clusters based on similarity. Additionally
asset nodes enriched with different metrics from Google Ads API and YouTube API to describe
features and performance metrics of creatives.

Data Visualization is a web application uniformly accessible for all users from http://filonov-ai.web.app.
It's deployed to Firebase Static Hosting and implemented as serverless web application where users
can open data files generated with the Data Pipeline.

## Filonov Data Pipeline

Entry point of the Data Pipeline is a CLI tool called `media-similarity`
that performs media tagging and assigns each medium its own cluster_id.

### Deployment

#### Prerequisites

- Python 3.8+
- A GCP project with billing account attached
- Either [Video Intelligence API](https://console.cloud.google.com/apis/library/videointelligence.googleapis.com) or [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) enabled (depending on type of media you want to analyze).

* [API key](https://support.google.com/googleapi/answer/6158862?hl=en) to access to access Google Gemini.

  - Once you created API key export it as an environmental variable

    ```
    export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
    ```

#### Installation

Install `media-similarity` library to perform media cluster assignments:

```
pip install -e libs/media_similarity/
```

#### Usage

```
media-similarity PATHS/TO/MEDIA --tagger <TAGGER_TYPE>  --db-uri <DATABASE_URI>
```

where:

- `PATHS/TO/MEDIA` - position arguments pointing to individual media files or URLs.
- TAGGER_TYPE - name of tagger, supported options:
  - `vision-api` - tags images based on [Google Cloud Vision API](https://cloud.google.com/vision/),
  - `video-api` for videos based on [Google Cloud Video Intelligence API](https://cloud.google.com/video-intelligence/)
  - `gemini-image` - Uses Gemini to tags images. Add `--tagger.n_tags=<N_TAGS>`
    parameter to control number of tags returned by tagger.
  - `gemini-video` - Uses Gemini to tags videos. Add `--tagger.n_tags=<N_TAGS>`
    parameter to control number of tags returned by tagger.
- `db-uri` - Connection string to the database with tagging results
  (i.e. `sqlite:///tagging.db`). Make sure that DB exists.
  > To create an empty Sqlite DB call `touch database.db`.

Here's an example command:

```
media-similarity media1.jpg media2.jpg media3.jpg \
  --tagger vision-api --db-uri sqlite:///tagging.db
```

Alternatively when reading from a file, you can execute the following command:

```
cat FILES_WITH_LINKS.txt | xargs media-similarity \
  --tagger-type <TAGGER_TYPE> --db-uri <DATABASE_URI>
```

where `FILES_WITH_LINKS.txt` contains either media paths or links to media.

## Filonov Data Visualization

To start using the visualization application we need to prepare graph data
using the Filonov Data Pipeline first. As a result we must get a json file,
which you'll open locally or via a remote link.

The web application is available at: http://filonov-ai.web.app.
It's completely serverless, as such there's no any authorization for accessing it,
it's publicly available.

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
