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
import json
from typing import Literal

import fastapi
import media_similarity
import media_tagging
import smart_open
import uvicorn
from media_similarity.entrypoints.server import (
  router as media_similarity_router,
)
from media_tagging.entrypoints.server import router as media_tagging_router
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

import filonov
from filonov.entrypoints import utils


class FilonovSettings(BaseSettings):
  """Specifies environmental variables for filonov.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    media_tagging_db_url: Connection string to DB with tagging results.
  """

  media_tagging_db_url: str | None = None


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


class CreativeMapGoogleAdsGenerateRequest(filonov.CreativeMapGenerateRequest):
  """Specifies Google Ads specific request for returning creative map."""

  input_parameters: filonov.inputs.google_ads.GoogleAdsInputParameters
  source: Literal['googleads'] = 'googleads'


class CreativeMapYouTubeGenerateRequest(filonov.CreativeMapGenerateRequest):
  """Specifies YouTube specific request for returning creative map."""

  input_parameters: filonov.inputs.youtube.YouTubeInputParameters
  source: Literal['youtube'] = 'youtube'
  media_type: Literal['YOUTUBE_VIDEO'] = 'YOUTUBE_VIDEO'
  tagger: Literal['gemini'] = 'gemini'


@router.post('/generate:googleads')
async def generate_creative_map_googleads(
  request: CreativeMapGoogleAdsGenerateRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates Json with creative map data."""
  return generate_creative_map(
    'googleads',
    request,
    dependencies,
  )


@router.post('/generate:youtube')
async def generate_creative_map_youtube(
  request: CreativeMapYouTubeGenerateRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates Json with creative map data."""
  return generate_creative_map(
    'youtube',
    request,
    dependencies,
  )


def generate_creative_map(
  source: Literal['youtube', 'googleads'],
  request: filonov.CreativeMapGenerateRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> filonov.creative_map.CreativeMapJson:
  """Generates Json with creative map data."""
  generated_map = (
    filonov.FilonovService(
      tagging_service=dependencies.tagging_service,
      similarity_service=dependencies.similarity_service,
    )
    .generate_creative_map(source, request)
    .to_json()
  )

  if request.output_parameters.output_type == 'file':
    destination = utils.build_creative_map_destination(
      request.output_parameters.output_name
    )
    with smart_open.open(destination, 'w', encoding='utf-8') as f:
      json.dump(generated_map, f)
    return fastapi.responses.JSONResponse(
      content=f'Creative map was saved to {destination}.'
    )

  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(generated_map)
  )


app = fastapi.FastAPI()
app.include_router(router)
app.include_router(media_tagging_router)
app.include_router(media_similarity_router)


def main():
  uvicorn.run(app)


if __name__ == '__main__':
  main()
