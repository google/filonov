# Copyright 2024 Google LLC
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
"""Provides HTTP endpoint for media tagging."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import fastapi
import typer
import uvicorn
from garf.executors.entrypoints import utils as garf_utils
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

import media_tagging
from media_tagging import (
  exceptions,
  media_tagging_service,
  repositories,
  taggers,
)
from media_tagging.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)

app = fastapi.FastAPI(
  title='Media Tagging API',
  version=media_tagging.__version__,
  description='Performs tagging of media based on various taggers',
)
FastAPIInstrumentor.instrument_app(app)
typer_app = typer.Typer()

OTEL_SERVICE_NAME = 'media-tagger'
initialize_tracer(OTEL_SERVICE_NAME)
meter = initialize_meter(OTEL_SERVICE_NAME)

logger = garf_utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(initialize_logger(OTEL_SERVICE_NAME))


class MediaTaggingSettings(BaseSettings):
  """Specifies environmental variables for media-tagger.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    media_tagging_db_url: Connection string to DB with tagging results.
  """

  media_tagging_db_url: str | None = None


class Dependencies:
  def __init__(self) -> None:
    """Initializes CommonDependencies."""
    settings = MediaTaggingSettings()
    self.tagging_service = media_tagging_service.MediaTaggingService(
      repositories.SqlAlchemyTaggingResultsRepository(
        settings.media_tagging_db_url
      )
    )


@app.post('/tag')
def tag(
  request: media_tagging_service.MediaTaggingRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> dict[str, str]:
  """Performs media tagging.

  Args:
    request: Post request for media tagging.
    dependencies: Common dependencies used by endpoint.

  Returns:
    Json results of tagging.
  """
  try:
    tagging_results = dependencies.tagging_service.tag_media(request)
    return fastapi.responses.JSONResponse(
      content=fastapi.encoders.jsonable_encoder(tagging_results)
    )
  except exceptions.MediaTaggingError as e:
    raise fastapi.HTTPException(status_code=404, detail=str(e))


@app.post('/describe')
def describe(
  request: media_tagging_service.MediaTaggingRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> dict[str, str]:
  """Performs media tagging.

  Args:
    request: Post request for media tagging.
    dependencies: Common dependencies used by endpoint.

  Returns:
    Json results of tagging.
  """
  try:
    tagging_results = dependencies.tagging_service.describe_media(request)
    return fastapi.responses.JSONResponse(
      content=fastapi.encoders.jsonable_encoder(tagging_results)
    )
  except exceptions.MediaTaggingError as e:
    raise fastapi.HTTPException(status_code=404, detail=str(e))


@app.get('/taggers')
def available_taggers() -> list[str]:
  return list(taggers.TAGGERS.keys())


@typer_app.command()
def main(
  port: Annotated[int, typer.Option(help='Port to start the server')] = 8000,
):
  uvicorn.run(app, host='0.0.0.0', port=port, log_config=None)


if __name__ == '__main__':
  typer_app()
