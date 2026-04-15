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

import celery
from garf.executors.entrypoints import utils as garf_utils
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


@celery.signals.worker_process_init.connect(weak=False)
def init_celery_telemetry(*args, **kwargs):
  otel_service_name = 'media-tagging-celery'
  initialize_tracer(otel_service_name)
  initialize_meter(otel_service_name)

  logger = garf_utils.init_logging(
    loglevel='INFO', logger_type='local', name=otel_service_name
  )
  logger.addHandler(initialize_logger(otel_service_name))
  CeleryInstrumentor().instrument()


@celery_app.task(pydantic=True)
def tag(
  request: media_tagging_service.MediaTaggingRequest,
) -> media_tagging_service.MediaTaggingResponse:
  return service.tag_media(request)


@celery_app.task(pydantic=True)
def describe(
  request: media_tagging_service.MediaTaggingRequest,
) -> media_tagging_service.MediaTaggingResponse:
  return service.describe_media(request)
