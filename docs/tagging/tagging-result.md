# Results of tagging

## TaggingResult

Once tagging is done you get a `TaggingResult`.

`TaggingResult` contains results of tagging for a single medium and contains the following elements:

* 	`processed_at` - time when medium was processed.
* 	`identifier` - unique identifier of medium. For file based media - base path without extension, for YouTube video - video_id, for texts - text itself.
* 	`type` - [type](media.md#supported-media-types) of medium.
* 	`content` - result of tagging. Can be either array of [Tag](#tag) or one or many [Descriptions](#description).
* 	`tagger` -  type of tagger used for tagging this medium.
* 	`output` - type of operation on medium  - either tag or description.
* 	`tagging_details` - Any details used to perform the tagging, for example custom_prompt, number of tags requested.



/// tab | tags
```python
from media_tagging import tagging_result

result = tagging_result.TaggingResult(
  tagger='gemini',
	type='IMAGE',
	output='tag',
	content=[
	  tagging_result.Tag(name='tag_name_1', score=1.0),
	  tagging_result.Tag(name='tag_name_1', score=0.1),
	],
	tagging_details={'n_tags': 2},
```

///

/// tab | description
```python
from media_tagging import tagging_result

result = tagging_result.TaggingResult(
  tagger='gemini',
	type='IMAGE',
	output='tag',
	content= tagging_result.Description(text='True'),
	tagging_details={
      'custom_prompt': 'Is this an advertising. Answer only True or False'
    },
```

///

/// tab | descriptions
```python
from media_tagging import tagging_result

result = tagging_result.TaggingResult(
  tagger='gemini',
	type='IMAGE',
	output='tag',
	content=
	  tagging_result.Description(text='00:00:05'),
	  tagging_result.Description(text='00:00:15'),
	],
	tagging_details={
      'custom_prompt': 'Find all the timestamps where a cat appears'
    },
```

///

You can extract tags / descriptions themself via `.content` property

```python
tags = results.content
```

## Tag

`Tag` represents a unique concept (using a singular noun) with a score from 0 to 1 where 0 is an absence of a concept and 1 is a total presence.

Usually a single media is tagged with multiple tags with varying scores.

```python
from media_tagging import tagging_result

tag = tagging_result.Tag(name='tag_name_1', score=0.1)
```

### Trimming tags

If `TaggingResult` contains tags you can trim them by removing those which scores lower than a custom threshold. This can be useful when `media-tagger` provides a lot of non-definitive tags.

```python
result.trim_tags(0.5)
```

## Description

`Description` contains an information on a media in a form of a text or JSON.

```python
from media_tagging import tagging_result

description = tagging_result.Description(text='This is an advertising.')
```
