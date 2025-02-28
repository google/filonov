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

import fastapi
import media_similarity
import media_tagging
import pydantic
import uvicorn
from media_similarity.entrypoints.server import (
  router as media_similarity_router,
)
from media_tagging.entrypoints.server import router as media_tagging_router
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

import filonov


class FilonovSettings(BaseSettings):
  media_tagging_db_url: str


class Dependencies:
  def __init__(self) -> None:
    """Initializes CommonDependencies."""
    settings = FilonovSettings()
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


router = fastapi.APIRouter(prefix='/creative_maps')


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


@router.post('/generate')
async def generate_creative_map(
  request: CreativeMapPostRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
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
  tagging_results = dependencies.tagging_service.tag_media(
    tagger_type=tagger,
    media_type=request.media_type,
    tagging_parameters={'n_tags': 100},
    media_paths=media_info.keys(),
  )
  clustering_results = dependencies.similarity_service.cluster_media(
    tagging_results, normalize=request.normalize
  )
  generated_map = filonov.CreativeMap.from_clustering(
    clustering_results, tagging_results, media_info, context
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(generated_map.to_json())
  )


app = fastapi.FastAPI()
app.include_router(router)
app.include_router(media_tagging_router)
app.include_router(media_similarity_router)


def main():
  uvicorn.run(app)


if __name__ == '__main__':
  main()
