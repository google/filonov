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
import pydantic
import typer
import uvicorn
from garf.executors.entrypoints import utils as garf_utils
from garf.io import writer
from media_tagging.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from typing_extensions import Annotated

import media_fetching
from media_fetching.sources import models

app = fastapi.FastAPI(
  title='Media Fetching API',
  version=media_fetching.__version__,
  description='Fetches media from various sources',
)
FastAPIInstrumentor.instrument_app(app)
typer_app = typer.Typer()

OTEL_SERVICE_NAME = 'media-fetching'
initialize_tracer(OTEL_SERVICE_NAME)
meter = initialize_meter(OTEL_SERVICE_NAME)

logger = garf_utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(initialize_logger(OTEL_SERVICE_NAME))


class WriterOptions(pydantic.BaseModel):
  writer: str = 'json'
  writer_parameters: dict[str, str] = pydantic.Field(default_factory=dict)
  output: str = 'media_results'


@app.post('/fetch:file')
async def fetch_file(
  request: media_fetching.sources.file.FileFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from a file."""
  return fetch('file', request, writer_options, enable_cache)


@app.post('/fetch:googleads')
async def fetch_googleads(
  request: media_fetching.sources.googleads.GoogleAdsFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from Google Ads."""
  return fetch('googleads', request, writer_options, enable_cache)


@app.post('/fetch:youtube')
async def fetch_youtube(
  request: media_fetching.sources.youtube.YouTubeFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from YouTube."""
  return fetch('youtube', request, writer_options, enable_cache)


@app.post('/fetch:bq')
async def fetch_bq(
  request: media_fetching.sources.sql.BigQueryFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from BigQuery."""
  return fetch('bq', request, writer_options, enable_cache)


@app.post('/fetch:sqldb')
async def fetch_sqldb(
  request: media_fetching.sources.sql.SqlAlchemyQueryFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from SqlAlchemy DB."""
  return fetch('sqldb', request, writer_options, enable_cache)


@app.post('/fetch:dbm')
async def fetch_dbm(
  request: media_fetching.sources.dbm.BidManagerFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from Bid Manager API."""
  return fetch('dbm', request, writer_options, enable_cache)


def fetch(
  source: str | models.InputSource,
  request: models.FetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
):
  """Fetches media data from a provided source."""
  fetching_service = media_fetching.MediaFetchingService.from_source_alias(
    source=source, enable_cache=enable_cache
  )
  report = fetching_service.fetch(request)
  return writer.create_writer(
    writer_options.writer, **writer_options.writer_parameters
  ).write(report, writer_options.output)


@typer_app.command()
def main(
  port: Annotated[int, typer.Option(help='Port to start the server')] = 8000,
):
  uvicorn.run(app, host='0.0.0.0', port=port, log_config=None)


if __name__ == '__main__':
  typer_app()
