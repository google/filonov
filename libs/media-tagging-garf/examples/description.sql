SELECT
  media_url,
  identifier AS text,
  content.text AS sentiment
FROM
  description
WHERE
  media_type = IMAGE
  AND tagger_type = 'gemini'
  AND media_paths IN ({media})
  AND tagging_options.custom_prompt = 'What is the sentiment of the media'
