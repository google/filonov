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
import media_fetching
import media_similarity
import media_tagging
from garf.executors.entrypoints import utils as garf_utils
from media_tagging.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)
from opentelemetry.instrumentation.celery import CeleryInstrumentor

import filonov
from filonov.entrypoints import utils

redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
media_tagging_db_url = os.getenv('MEDIA_TAGGING_DB_URL')
similarity_db_url = os.getenv('SIMILARITY_DB_URL', media_tagging_db_url)


@celery.signals.worker_process_init.connect(weak=False)
def init_celery_telemetry(*args, **kwargs):
  otel_service_name = 'filonov-celery'
  initialize_tracer(otel_service_name)
  initialize_meter(otel_service_name)

  logger = garf_utils.init_logging(
    loglevel='INFO', logger_type='local', name=otel_service_name
  )
  logger.addHandler(initialize_logger(otel_service_name))
  CeleryInstrumentor().instrument()


app = celery.Celery(
  'filonov',
  broker=redis_url,
  backend=redis_url,
)

tagging_service = media_tagging.MediaTaggingService(
  media_tagging.repositories.SqlAlchemyTaggingResultsRepository(
    media_tagging_db_url
  )
)

similarity_service = media_similarity.MediaSimilarityService(
  media_similarity_repository=(
    media_similarity.repositories.SqlAlchemySimilarityPairsRepository(
      similarity_db_url
    )
  )
)


@app.task(pydantic=True)
def create_map(
  request: filonov.GenerateCreativeMapRequest,
) -> filonov.creative_map.CreativeMap:
  """Writes filonov data to creative map."""
  generated_map = filonov.FilonovService(
    fetching_service=media_fetching.MediaFetchingService.from_source_alias(
      **request.source_parameters.model_dump()
    ),
    tagging_service=tagging_service,
    similarity_service=similarity_service,
  ).generate_creative_map(request)
  if request.output_type == 'file':
    destination = utils.build_creative_map_destination(request.output_name)
    generated_map.save(destination)
    return {'location': str(destination)}
  return generated_map.to_json()


@app.task(pydantic=True)
def create_tables(
  request: filonov.GenerateTablesRequest,
) -> dict[str, str]:
  """Writes filonov data to tables."""
  return filonov.FilonovService(
    fetching_service=media_fetching.MediaFetchingService.from_source_alias(
      **request.source_parameters.model_dump()
    ),
    tagging_service=tagging_service,
    similarity_service=similarity_service,
  ).generate_tables(request)
