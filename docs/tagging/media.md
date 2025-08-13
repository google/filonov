# What is Media?

Media represent files, texts, etc. which contains audio-visual elements.

Each media consist of several elements:

* `media_path` - location where media can be found.
* `media_type` - type of media, see [supported media types](#supported-media-types).
* `name` - optional name of the media, if not specified then name of base file name is used for file-based media.
* `content` - optional byte representation of a medium.

## Supported media types

* IMAGE
* VIDEO
* TEXT
* YOUTUBE_VIDEO


Media can be located somewhere (local file, GCS / S3 bucket, URL) or present as it (i.e. text).
