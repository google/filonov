# Copyright 2026 Google LLC
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

import os
from typing import Any

import celery
import pydantic
from garf.executors.entrypoints import utils as garf_utils
from garf.io import writer as garf_writer
from opentelemetry.instrumentation.celery import CeleryInstrumentor

from media_tagging import media_tagging_service, repositories
from media_tagging.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)

redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
media_tagging_db_url = os.getenv('MEDIA_TAGGING_DB_URL')
celery_app = celery.Celery(
  'worker',
  broker=redis_url,
  backend=redis_url,
)


service = media_tagging_service.MediaTaggingService(
  repositories.SqlAlchemyTaggingResultsRepository(media_tagging_db_url)
)


class TaggingRequest(media_tagging_service.MediaTaggingRequest):
  writer: garf_writer.WriterOption | None = None
  writer_parameters: dict[str, Any] = pydantic.Field(default_factory=dict)
  output: str = 'tagging_results'


@celery.signals.worker_process_init.connect(weak=False)
def init_celery_telemetry(*args, **kwargs):
  otel_service_name = os.getenv('OTEL_SERVICE_NAME', 'media-tagging-celery')
  initialize_tracer(otel_service_name)
  initialize_meter(otel_service_name)

  logger = garf_utils.init_logging(
    loglevel=os.getenv('OTEL_LOG_LEVEL', 'INFO'),
    logger_type='local',
    name=otel_service_name,
  )
  logger.addHandler(initialize_logger(otel_service_name))
  CeleryInstrumentor().instrument()


@celery_app.task(pydantic=True)
def tag(
  request: TaggingRequest,
) -> media_tagging_service.MediaTaggingResponse:
  response = service.tag_media(request)
  if request.writer:
    return response.save(
      request.output, request.writer, **request.writer_parameters
    )
  return response


@celery_app.task(pydantic=True)
def describe(
  request: TaggingRequest,
) -> media_tagging_service.MediaTaggingResponse:
  response = service.describe_media(request)
  if request.writer:
    return response.save(
      request.output, request.writer, **request.writer_parameters
    )
  return response
