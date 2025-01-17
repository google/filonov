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
"""Provides HTTP endpoint for media similarity requests."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import dataclasses
import os

import fastapi
import media_tagging
import pydantic

import media_similarity

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


class MediaClusteringPostRequest(pydantic.BaseModel):
  """Specifies structure of request for tagging media.

  Attributes:
    media_paths: Identifiers or media to cluster (file names or links).
    normalize: Whether to apply normalization threshold.
  """

  media_paths: list[str]
  tagger_type: str = 'vision-api'
  normalize: bool = True


@app.post('/cluster')
async def cluster_media(
  request: MediaClusteringPostRequest,
) -> dict[str, int]:
  """Performs media clustering."""
  tagging_results = tagging_service.tag_media(
    tagger_type=request.tagger_type, media_paths=request.media_paths
  )
  clustering_results = similarity_service.cluster_media(
    tagging_results, normalize=request.normalize
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(clustering_results.clusters)
  )


@app.get('/search')
async def search_media(
  seed_media_identifier: str,
  n_results: int = 10,
) -> dict[str, str]:
  """Searches for similar media based on a provided seed media identifier.

  Args:
    seed_media_identifier: Media identifier to (file name of link).
    n_results: How many similar media to return.

  Returns:
    Top n identifiers for similar media.
  """
  results = similarity_service.find_similar_media(
    seed_media_identifier, n_results
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(dataclasses.asdict(results))
  )
