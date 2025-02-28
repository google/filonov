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
import pydantic
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
  """

  media_tagging_db_url: str | None = None


class Dependencies:
  def __init__(self) -> None:
    """Initializes CommonDependencies."""
    settings = MediaSimilaritySettings()
    self.tagging_service = media_tagging.MediaTaggingService(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
        settings.media_tagging_db_url
      )
    )
    self.similarity_service = media_similarity.MediaSimilarityService(
      media_similarity_repository=(
        media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
          settings.media_tagging_db_url
        )
      ),
    )


class MediaClusteringPostRequest(pydantic.BaseModel):
  """Specifies structure of request for tagging media.

  Attributes:
    media_paths: Identifiers or media to cluster (file names or links).
    media_type: Type of media found in media_paths.
    tagger_type: Type of tagger to use if media tags are not found.
    normalize: Whether to apply normalization threshold.
  """

  media_paths: list[str]
  media_type: str
  tagger_type: str = 'gemini'
  normalize: bool = True


@router.post('/cluster')
async def cluster_media(
  request: MediaClusteringPostRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> dict[str, int]:
  """Performs media clustering."""
  tagging_results = dependencies.tagging_service.tag_media(
    tagger_type=request.tagger_type,
    media_type=request.media_type,
    media_paths=request.media_paths,
  )
  clustering_results = dependencies.similarity_service.cluster_media(
    tagging_results, normalize=request.normalize
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(clustering_results.clusters)
  )


@router.get('/search')
async def search_media(
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
  seed_media_identifiers: str,
  media_type: str = 'UNKNOWN',
  n_results: int = 10,
) -> dict[str, str]:
  """Searches for similar media based on provided seed media identifiers.

  Args:
    dependencies: Common dependencies injected.
    seed_media_identifiers: Comma separated file names or links.
    media_type: Type of media to search for.
    n_results: How many similar media to return for each seed identifier.

  Returns:
    Top n identifiers for similar media.
  """
  seed_media_identifiers = [
    media_tagging.media.convert_path_to_media_name(
      seed_media_identifier.strip(),
      media_type,
    )
    for seed_media_identifier in seed_media_identifiers.split(',')
  ]
  similar_media = dependencies.similarity_service.find_similar_media(
    seed_media_identifiers, n_results
  )
  results = {
    result.seed_media_identifier: result.results for result in similar_media
  }
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(results)
  )


app = fastapi.FastAPI()
app.include_router(router)

if __name__ == '__main__':
  uvicorn.run(app)
