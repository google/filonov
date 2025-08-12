# Results of tagging

## TaggingResult

Once tagging is done you get a `TaggingResult`.

`TaggingResult` contains results of tagging for a single medium and contains the following elements:

* 	`processed_at` - time when medium was processed
* 	`identifier` - unique identifier of medium. For file based media - base path without extension, for YouTube video - video_id, for texts - text itself.
* 	`type` - type of medium
* 	`content` - result of tagging. Can be either tags or description(s).
* 	`tagger` -  type of tagger used for tagging this medium.
* 	`output` - type of operation on medium  - either tag or description.
* 	`tagging_details` - Any details used to perform the tagging, for example custom_prompt, number of tags requested.



```python
from media_tagging import tagging_result

result = TaggingResult(
  tagger='gemini',
	type='IMAGE',
	output='tag',
	content=[
	  tagging_result.Tag(name='tag_name_1', score=1.0),
	  tagging_result.Tag(name='tag_name_1', score=0.1),
	],
	tagging_details={'n_tags': 2},
```

### Trimming tags

If `TaggingResult` contains tags you can trim them by removing those which scores lower than a custom threshold. This can be useful when `media-tagger` provides a lot of non-definitive tags.

```python
result.trim_tags(0.5)

```
