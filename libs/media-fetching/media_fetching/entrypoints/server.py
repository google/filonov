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
import uvicorn
from garf_io import writer

import media_fetching
from media_fetching.sources import models

router = fastapi.APIRouter(prefix='/media_fetching')


class WriterOptions(pydantic.BaseModel):
  writer: str = 'json'
  writer_parameters: dict[str, str] = pydantic.Field(default_factory=dict)
  output: str = 'media_results'


@router.post('/fetch:file')
async def fetch_file(
  request: media_fetching.sources.file.FileFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from a file."""
  return fetch('file', request, writer_options, enable_cache)


@router.post('/fetch:googleads')
async def fetch_googleads(
  request: media_fetching.sources.googleads.GoogleAdsFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from Google Ads."""
  return fetch('googleads', request, writer_options, enable_cache)


@router.post('/fetch:youtube')
async def fetch_youtube(
  request: media_fetching.sources.youtube.YouTubeFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from YouTube."""
  return fetch('youtube', request, writer_options, enable_cache)


@router.post('/fetch:bq')
async def fetch_bq(
  request: media_fetching.sources.sql.BigQueryFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from BigQuery."""
  return fetch('bq', request, writer_options, enable_cache)


@router.post('/fetch:sqldb')
async def fetch_sqldb(
  request: media_fetching.sources.sql.SqlAlchemyQueryFetchingParameters,
  writer_options: WriterOptions,
  enable_cache: bool = False,
) -> fastapi.responses.JSONResponse:
  """Fetches media data from SqlAlchemy DB."""
  return fetch('sqldb', request, writer_options, enable_cache)


@router.post('/fetch:dbm')
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


app = fastapi.FastAPI()
app.include_router(router)


def main():
  uvicorn.run(app)


if __name__ == '__main__':
  main()
