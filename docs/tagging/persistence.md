# Save results of tagging in DB

By default when doing tagging all intermediate data is saved in the memory.

You can opt-in to persisting data in the database of your choice.

If you're tagging the same media and the same tagger for the second time its tags will be fetched
from DB instead of calling API to perform the tagging..

/// tab | cli
```bash
media-tagger tag MEDIA_PATHs \
  --media-type IMAGE \
  --tagger gemini \
  --db-uri sqlite:///tagging.db \
  --writer csv \
  --output tagging_results
```
///

/// tab | python
```python
import media_tagging
from media_tagging.repositories import SqlAlchemyTaggingResultsRepository

repository = SqlAlchemyTaggingResultsRepository('sqlite:///tagging.db')
media_tagger = media_tagging.MediaTaggingService(repository)

result = media_tagger.tag_media(
  media_type='IMAGE',
  media_paths=['image1.png', 'image2.png'],
  tagger_type='gemini',
)
```
///
