# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provides HTTP endpoint for filonov requests."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import os

import fastapi
import media_similarity
import media_tagging
import pydantic

import filonov

app = fastapi.FastAPI()

media_db_uri = os.getenv('MEDIA_TAGGING_DB_URL')
tagging_service = media_tagging.MediaTaggingService(
  tagging_results_repository=(
    media_tagging.repositories.SqlAlchemyTaggingResultsRepository(media_db_uri)
  )
)
similarity_service = media_similarity.MediaSimilarityService(
  media_similarity_repository=(
    media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
      media_db_uri
    )
  ),
)


class CreativeMapPostRequest(pydantic.BaseModel):
  """Specifies structure of request for returning creative map.

  Attributes:
    source: Source of getting data for creative map.
    media_type: Type of media to get.
    input_parameters: Parameters to get data from the source.
    tagger: Type of tagger to use.
    normalize: Whether to apply normalization threshold.
  """

  source: str
  media_type: str
  input_parameters: dict[str, str]
  tagger: str | None = None
  normalize: bool = True


@app.post('/creative_map')
async def generate_creative_map(
  request: CreativeMapPostRequest,
) -> filonov.creative_map.CreativeMapJson:
  """Generates Json with creative map data."""
  input_service = filonov.MediaInputService(request.source)
  media_info, context = input_service.generate_media_info(
    request.media_type, request.input_parameters
  )
  if request.tagger is None:
    tagger = f'gemini-{request.media_type.lower()}'
  else:
    tagger = request.tagger
  tagging_results = tagging_service.tag_media(
    tagger_type=tagger, media_paths=media_info.keys()
  )
  clustering_results = similarity_service.cluster_media(
    tagging_results, normalize=request.normalize
  )
  generated_map = filonov.CreativeMap.from_clustering(
    clustering_results, tagging_results, media_info, context
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(generated_map.to_json())
  )
