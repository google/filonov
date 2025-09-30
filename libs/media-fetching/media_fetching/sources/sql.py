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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Defines fetching data from a DB."""

from collections.abc import Sequence
from typing import Literal

import pydantic
from garf_core import report
from garf_executors import bq_executor, sql_executor

from media_fetching.sources import models


class TableFetchingParameters(models.FetchingParameters):
  """SQL table specific parameters for getting media."""

  table: str
  media_type: Literal['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO', None] = None
  media_identifier: str = 'media_url'
  media_name: str = 'media_name'
  metrics: Sequence[str] | str = ('clicks', 'impressions')
  segments: Sequence[str] | str | None = None
  extra_info: Sequence[str] | None = pydantic.Field(default_factory=list)

  @property
  def query_text(self) -> str:
    fields = f'{self.media_identifier}, {self.media_name}'
    if self.metrics:
      metrics = ', '.join(self.metrics)
      if metrics:
        fields = f'{fields}, {metrics}'
    if self.segments:
      segments = ', '.join(self.segments)
      if segments:
        fields = f'{fields}, {segments}'
    return f'SELECT {fields} FROM {self.table}'

  def model_post_init(self, __context__):
    if isinstance(self.metrics, str):
      self.metrics = self.metrics.split(',')
    if isinstance(self.segments, str):
      self.segments = self.segments.split(',')


class BigQueryFetchingParameters(TableFetchingParameters):
  """BigQuery specific parameters for getting media."""

  @property
  def project(self) -> str:
    return self.table.split('.')[0]


class SqlAlchemyQueryFetchingParameters(TableFetchingParameters):
  """SqlAlchemy specific parameters for getting media."""

  connection_string: str = pydantic.Field(exclude=True)


class BigQueryFetcher(models.BaseMediaInfoFetcher):
  """Extracts information from a BigQuery table into a media report."""

  def fetch_media_data(
    self,
    fetching_request: BigQueryFetchingParameters,
  ) -> report.GarfReport:
    executor = bq_executor.BigQueryExecutor(
      project_id=fetching_request.project,
    )
    return executor.execute(
      title='media_data', query=fetching_request.query_text
    )


class SqlAlchemyQueryFetcher(models.BaseMediaInfoFetcher):
  """Extracts information from a SQL database into a media report."""

  def fetch_media_data(
    self,
    fetching_request: SqlAlchemyQueryFetchingParameters,
  ) -> report.GarfReport:
    executor = sql_executor.SqlAlchemyQueryExecutor.from_connection_string(
      connection_string=fetching_request.connection_string
    )
    return executor.execute(
      title='media_data', query=fetching_request.query_text
    )
