SELECT
  media_url,
  identifier AS text,
  content[].name AS tags_names,
  content AS tags
FROM
  tag
WHERE
  media_type = IMAGE
  AND tagger_type = 'gemini'
  AND media_paths IN ({media})
