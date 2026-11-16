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

"""Opentelemetry initialization functions."""

import os
from typing import Optional

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
  OTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
  OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
  OTLPSpanExporter,
)
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
  PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

DEFAULT_SERVICE_NAME = 'media-tagging'


def _init_resource(
  otel_service_name: Optional[str] = None,
  extra_attributes: dict[str, int | str] | None = None,
) -> Resource:
  env_resource = Resource.create()
  attributes = {
    SERVICE_NAME: otel_service_name
    or os.getenv('OTEL_SERVICE_NAME', DEFAULT_SERVICE_NAME),
  }
  if extra_attributes:
    attributes.update(extra_attributes)
  if mode := os.getenv('MEDIA_TAGGING_MODE'):
    attributes['media_tagging.mode'] = mode
  library_resource = Resource(attributes=attributes)
  return env_resource.merge(library_resource)


def initialize_tracer(
  service_name: str | None = None,
  extra_attributes: dict[str, int | str] | None = None,
) -> None:
  """Initializes tracer based on a provided service name.

  If OTEL_EXPORTER_OTLP_ENDPOINT ENV variable is set, traces are exported
  to a specified endpoint.

  Returns:
    Initialized tracer provider.
  """
  resource = _init_resource(service_name, extra_attributes)

  tracer_provider = TracerProvider(resource=resource)

  if otel_endpoint := os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    otlp_processor = BatchSpanProcessor(
      OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
    )
    tracer_provider.add_span_processor(otlp_processor)
  return tracer_provider


def initialize_meter(
  service_name: str | None = None,
  extra_attributes: dict[str, int | str] | None = None,
) -> MeterProvider:
  """Initializes meter based on a provided service name.

  If OTEL_EXPORTER_OTLP_ENDPOINT ENV variable is set, metrics are exported
  to a specified endpoint.

  Returns:
    Initialized meter provider.
  """
  resource = _init_resource(service_name, extra_attributes)
  meter_provider = MeterProvider(resource=resource)

  if otel_endpoint := os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    metric_exporter = OTLPMetricExporter(endpoint=f'{otel_endpoint}/v1/metrics')
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(
      resource=resource, metric_readers=[metric_reader]
    )
  else:
    meter_provider = MeterProvider(resource=resource)
  return meter_provider


def initialize_logger(
  service_name: str | None = None,
  extra_attributes: dict[str, int | str] | None = None,
):
  """Initializes logger handler based on a provided service name.

  If OTEL_EXPORTER_OTLP_ENDPOINT ENV variable is set, logs are exported
  to a specified endpoint.

  Returns:
    Initialized logger handler.
  """
  resource = _init_resource(service_name, extra_attributes)
  logger_provider = LoggerProvider(resource=resource)
  if otel_endpoint := os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
    log_exporter = OTLPLogExporter(endpoint=otel_endpoint, insecure=True)
    logger_provider.add_log_record_processor(
      BatchLogRecordProcessor(log_exporter)
    )
  return logger_provider
