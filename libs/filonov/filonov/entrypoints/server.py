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
from typing import Literal

import fastapi
import media_fetching
import media_similarity
import media_tagging
import typer
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
    similarity_db_uri: Connection string to DB with similarity results.
    filonov_enable_cache: Whether to get media data from a cache.
  """

  media_tagging_db_url: str | None = None
  similarity_db_url: str | None = None
  filonov_enable_cache: bool = False


class Dependencies:
  def __init__(self) -> None:
    """Initializes CommonDependencies."""
    settings = FilonovSettings()
    self.tagging_service = media_tagging.MediaTaggingService(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
        settings.media_tagging_db_url
      )
    )
    similarity_db_url = (
      settings.similarity_db_url or settings.media_tagging_db_url
    )
    self.similarity_service = media_similarity.MediaSimilarityService(
      media_similarity_repository=(
        media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
          similarity_db_url
        )
      ),
      tagging_service=media_tagging.MediaTaggingService(
        media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
          settings.media_tagging_db_url
        )
      ),
    )
    self.enable_cache = settings.filonov_enable_cache


creative_map_router = fastapi.APIRouter(prefix='/filonov/creative_map')
dashboard_router = fastapi.APIRouter(prefix='/filonov/dashboard')


class GenerateTablesGoogleAdsRequest(filonov.GenerateTablesRequest):
  """Specifies Google Ads specific request for dashboard generation."""

  source_parameters: (
    media_fetching.sources.googleads.GoogleAdsFetchingParameters
  )
  source: Literal['googleads'] = 'googleads'


class GenerateCreativeMapGoogleAdsRequest(filonov.GenerateCreativeMapRequest):
  """Specifies Google Ads specific request for returning creative map."""

  source_parameters: (
    media_fetching.sources.googleads.GoogleAdsFetchingParameters
  )
  source: Literal['googleads'] = 'googleads'


class GenerateTablesFileRequest(filonov.GenerateTablesRequest):
  """Specifies file specific request for dashboard generation."""

  source_parameters: media_fetching.sources.file.FileFetchingParameters
  source: Literal['file'] = 'file'


class GenerateCreativeMapFileRequest(filonov.GenerateCreativeMapRequest):
  """Specifies Google Ads specific request for returning creative map."""

  source_parameters: media_fetching.sources.file.FileFetchingParameters
  source: Literal['file'] = 'file'


class GenerateTablesYouTubeRequest(filonov.GenerateTablesRequest):
  """Specifies YouTube specific request for dashboard generation."""

  source_parameters: media_fetching.sources.youtube.YouTubeFetchingParameters
  source: Literal['youtube'] = 'youtube'
  media_type: Literal['YOUTUBE_VIDEO'] = 'YOUTUBE_VIDEO'
  tagger: Literal['gemini'] = 'gemini'


class GenerateCreativeMapYouTubeRequest(filonov.GenerateCreativeMapRequest):
  """Specifies YouTube specific request for returning creative map."""

  source_parameters: media_fetching.sources.youtube.YouTubeFetchingParameters
  source: Literal['youtube'] = 'youtube'
  media_type: Literal['YOUTUBE_VIDEO'] = 'YOUTUBE_VIDEO'
  tagger: Literal['gemini'] = 'gemini'


class GenerateTablesBidManagerRequest(filonov.GenerateTablesRequest):
  """Specifies file specific request for dashboard generation."""

  source_parameters: media_fetching.sources.dbm.BidManagerFetchingParameters
  source: Literal['dbm'] = 'dbm'


class GenerateCreativeMapBidManagerRequest(filonov.GenerateCreativeMapRequest):
  """Specifies Google Ads specific request for returning creative map."""

  source_parameters: media_fetching.sources.dbm.BidManagerFetchingParameters
  source: Literal['dbm'] = 'dbm'


@dashboard_router.post('/file')
def generate_tables_file(
  request: GenerateTablesFileRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources based on a file."""
  return generate_tables(
    'file',
    request,
    dependencies,
  )


@creative_map_router.post('/file')
def generate_creative_map_file(
  request: GenerateCreativeMapFileRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on a file."""
  return generate_creative_map(
    'file',
    request,
    dependencies,
  )


@dashboard_router.post('/googleads')
def generate_tables_googleads(
  request: GenerateTablesGoogleAdsRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources based on Google Ads."""
  return generate_tables(
    'googleads',
    request,
    dependencies,
  )


@creative_map_router.post('/googleads')
def generate_creative_map_googleads(
  request: GenerateCreativeMapGoogleAdsRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on Google Ads."""
  return generate_creative_map(
    'googleads',
    request,
    dependencies,
  )


@dashboard_router.post('/youtube')
def generate_tables_youtube(
  request: GenerateTablesYouTubeRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources JSON based on YouTube channel."""
  return generate_tables(
    'youtube',
    request,
    dependencies,
  )


@creative_map_router.post('/youtube')
def generate_creative_map_youtube(
  request: GenerateCreativeMapYouTubeRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on YouTube channel."""
  return generate_creative_map(
    'youtube',
    request,
    dependencies,
  )


@dashboard_router.post('/dbm')
def generate_tables_dbm(
  request: GenerateTablesBidManagerRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources JSON based on BidManager API."""
  return generate_tables(
    'dbm',
    request,
    dependencies,
  )


@creative_map_router.post('/dbm')
def generate_creative_map_dbm(
  request: GenerateCreativeMapBidManagerRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on BidManager API."""
  return generate_creative_map(
    'dbm',
    request,
    dependencies,
  )


def generate_creative_map(
  source: Literal['youtube', 'googleads', 'file'],
  request: filonov.GenerateCreativeMapRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> filonov.creative_map.CreativeMapJson:
  """Generates creative map JSON based on provided source."""
  generated_map = filonov.FilonovService(
    fetching_service=media_fetching.MediaFetchingService.from_source_alias(
      source=source,
      enable_cache=dependencies.enable_cache
      or bool(request.source_parameters.get('enable_cache')),
    ),
    tagging_service=dependencies.tagging_service,
    similarity_service=dependencies.similarity_service,
  ).generate_creative_map(request)

  if request.output_type == 'file':
    destination = utils.build_creative_map_destination(
      request.output_parameters.output_name
    )
    generated_map.save(destination)
    return fastapi.responses.JSONResponse(
      content=f'Creative map was saved to {destination}.'
    )

  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(generated_map.to_json())
  )


def generate_tables(
  source: Literal['youtube', 'googleads', 'file', 'dbm'],
  request: filonov.GenerateTablesRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> filonov.creative_map.CreativeMapJson:
  """Writes filonov data."""
  (
    filonov.FilonovService(
      fetching_service=media_fetching.MediaFetchingService.from_source_alias(
        source=source,
        enable_cache=dependencies.enable_cache
        or bool(request.source_parameters.get('enable_cache')),
      ),
      tagging_service=dependencies.tagging_service,
      similarity_service=dependencies.similarity_service,
    ).generate_tables(request)
  )
  return fastapi.responses.JSONResponse(content='sources have been created.')


app = fastapi.FastAPI()
app.include_router(creative_map_router)
app.include_router(dashboard_router)
app.include_router(media_tagging_router)
app.include_router(media_similarity_router)

typer_app = typer.Typer()


@typer_app.command()
def main(
  port: Annotated[int, typer.Option(help='Port to start the server')] = 8000,
):
  uvicorn.run(app, port=port)


if __name__ == '__main__':
  typer_app()
