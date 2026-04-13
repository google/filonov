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
from garf.executors.entrypoints import utils as garf_utils
from media_tagging.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

import filonov
from filonov.entrypoints import tasks

app = fastapi.FastAPI(
  title='Filonov API',
  version=filonov.__version__,
  description='API for creative analysis',
)
FastAPIInstrumentor.instrument_app(app)

typer_app = typer.Typer()

OTEL_SERVICE_NAME = 'filonov'
initialize_tracer(OTEL_SERVICE_NAME)
meter = initialize_meter(OTEL_SERVICE_NAME)

logger = garf_utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(initialize_logger(OTEL_SERVICE_NAME))


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


@app.get('/api/version')
async def version() -> str:
  return filonov.__version__


@app.get('/api/info')
async def info() -> dict[str, str]:
  return {
    'filonov': filonov.__version__,
    'media_tagging': media_tagging.__version__,
    'media_fetching': media_fetching.__version__,
    'media_similarity': media_similarity.__version__,
  }


@app.get('/api/operations/{operation_id}')
def operation_status(operation_id: str):
  """Gets tagging operation status and results."""
  operation = tasks.app.AsyncResult(operation_id)
  return {
    'operation_id': operation_id,
    'status': operation.status,
    'results': operation.result if operation.status == 'SUCCESS' else None,
  }


@app.post('/api/dashboard/file:task')
def tag_task(
  request: GenerateTablesFileRequest,
) -> dict[str, str]:
  """Sends file-based dashboard generating request to Celery.

  Args:
    request: Post request for generating dashboard based on file input.

  Returns:
    Operation id and its status.
  """
  task = tasks.create_tables.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/dashboard/file')
@app.post('/dashboard/file', deprecated=True)
def generate_tables_file(
  request: GenerateTablesFileRequest,
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources based on a file."""
  return generate_tables(request)


@app.post('/api/creative_map/file:task')
def generate_creative_map_file_task(
  request: GenerateCreativeMapFileRequest,
) -> dict[str, str]:
  """Generates creative map JSON based on a file."""
  task = tasks.create_map.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/creative_map/file')
@app.post('/creative_map/file', deprecated=True)
def generate_creative_map_file(
  request: GenerateCreativeMapFileRequest,
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on a file."""
  return generate_creative_map(request)


@app.post('/api/dashboard/googleads:task')
def generate_tables_googleads_task(
  request: GenerateTablesGoogleAdsRequest,
) -> dict[str, str]:
  """Generates dashboard sources based on Google Ads."""
  task = tasks.create_tables.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/dashboard/googleads')
@app.post('/dashboard/googleads', deprecated=True)
def generate_tables_googleads(
  request: GenerateTablesGoogleAdsRequest,
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources based on Google Ads."""
  return generate_tables(request)


@app.post('/api/creative_map/googleads:task')
def generate_creative_map_googleads_task(
  request: GenerateCreativeMapGoogleAdsRequest,
) -> dict[str, str]:
  """Generates creative map JSON based on Google Ads."""
  task = tasks.create_map.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/creative_map/googleads')
@app.post('/creative_map/googleads', deprecated=True)
def generate_creative_map_googleads(
  request: GenerateCreativeMapGoogleAdsRequest,
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on Google Ads."""
  return generate_creative_map(request)


@app.post('/api/dashboard/youtube:task')
def generate_tables_youtube_task(
  request: GenerateTablesYouTubeRequest,
) -> dict[str, str]:
  """Generates dashboard sources JSON based on YouTube channel."""
  task = tasks.create_tables.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/dashboard/youtube')
@app.post('/dashboard/youtube', deprecated=True)
def generate_tables_youtube(
  request: GenerateTablesYouTubeRequest,
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources JSON based on YouTube channel."""
  return generate_tables(request)


@app.post('/api/creative_map/youtube:task')
def generate_creative_map_youtube_task(
  request: GenerateCreativeMapYouTubeRequest,
) -> dict[str, str]:
  """Generates creative map JSON based on YouTube channel."""
  task = tasks.create_map.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/creative_map/youtube')
@app.post('/creative_map/youtube', deprecated=True)
def generate_creative_map_youtube(
  request: GenerateCreativeMapYouTubeRequest,
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on YouTube channel."""
  return generate_creative_map(request)


@app.post('/api/dashboard/dbm:task')
def generate_tables_dbm_task(
  request: GenerateTablesBidManagerRequest,
) -> dict[str, str]:
  """Generates dashboard sources JSON based on BidManager API."""
  task = tasks.create_tables.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/dashboard/dbm')
@app.post('/dashboard/dbm', deprecated=True)
def generate_tables_dbm(
  request: GenerateTablesBidManagerRequest,
) -> fastapi.responses.JSONResponse:
  """Generates dashboard sources JSON based on BidManager API."""
  return generate_tables(request)


@app.post('/api/creative_map/dbm:task')
def generate_creative_map_dbm_task(
  request: GenerateCreativeMapBidManagerRequest,
) -> dict[str, str]:
  """Generates creative map JSON based on BidManager API."""
  task = tasks.create_map.delay(request.model_dump())
  return {'operation_id': task.id, 'status': 'PENDING'}


@app.post('/api/creative_map/dbm')
@app.post('/creative_map/dbm', deprecated=True)
def generate_creative_map_dbm(
  request: GenerateCreativeMapBidManagerRequest,
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on BidManager API."""
  return generate_creative_map(request)


def generate_creative_map(
  request: filonov.GenerateCreativeMapRequest,
) -> fastapi.responses.JSONResponse:
  """Generates creative map JSON based on provided source."""
  generated_map = tasks.create_map(request)
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(generated_map)
  )


def generate_tables(
  request: filonov.GenerateTablesRequest,
) -> fastapi.responses.JSONResponse:
  """Writes filonov data."""
  file_locations = tasks.create_tables(request)
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(file_locations)
  )


@typer_app.command()
def main(
  port: Annotated[int, typer.Option(help='Port to start the server')] = 8000,
):
  uvicorn.run(app, host='0.0.0.0', port=port, log_config=None)


if __name__ == '__main__':
  typer_app()
