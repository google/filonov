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

import fastapi
import media_tagging
import uvicorn
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

import media_similarity

router = fastapi.APIRouter(prefix='/media_similarity')


class MediaSimilaritySettings(BaseSettings):
  """Specifies environmental variables for media-similarity.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    media_tagging_db_url: Connection string to DB with tagging results.
    similarity_db_uri: Connection string to DB with similarity results.
  """

  media_tagging_db_url: str | None = None
  similarity_db_url: str | None = None


class Dependencies:
  def __init__(self) -> None:
    """Initializes CommonDependencies."""
    settings = MediaSimilaritySettings()
    self.similarity_service = media_similarity.MediaSimilarityService(
      media_similarity_repository=(
        media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
          settings.similarity_db_url or settings.media_tagging_db_url
        )
      ),
      tagging_service=media_tagging.MediaTaggingService(
        media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
          settings.media_tagging_db_url
        )
      ),
    )


@router.post('/cluster')
async def cluster_media(
  request: media_similarity.MediaClusteringRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Performs media clustering."""
  clustering_results = dependencies.similarity_service.cluster_media(request)
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(clustering_results.clusters)
  )


@router.get('/search')
async def search_media(
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
  seed_media_identifiers: str,
  media_type: str = 'UNKNOWN',
  n_results: int = 10,
) -> fastapi.responses.JSONResponse:
  """Searches for similar media based on provided seed media identifiers.

  Args:
    dependencies: Common dependencies injected.
    seed_media_identifiers: Comma separated file names or links.
    media_type: Type of media to search for.
    n_results: How many similar media to return for each seed identifier.

  Returns:
    Top n identifiers for similar media.
  """
  request = media_similarity.MediaSimilaritySearchRequest(
    media_paths=seed_media_identifiers.split(','),
    media_type=media_type,
    n_results=n_results,
  )
  similar_media = dependencies.similarity_service.find_similar_media(request)
  results = {
    result.seed_media_identifier: result.results for result in similar_media
  }
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(results)
  )


@router.post('/compare')
async def compare_media(
  request: media_similarity.MediaSimilarityComparisonRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Performs comparison between all media pairs.

  Args:
    request: Request for performing media comparison.
    dependencies: Common dependencies injected.

  Returns:
    Top n identifiers for similar media.
  """
  media_comparison_results = dependencies.similarity_service.compare_media(
    request
  )
  results = {
    result.media_pair_identifier: result.similarity_score.model_dump()
    for result in media_comparison_results
  }
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(results)
  )


app = fastapi.FastAPI()
app.include_router(router)

if __name__ == '__main__':
  uvicorn.run(app)
