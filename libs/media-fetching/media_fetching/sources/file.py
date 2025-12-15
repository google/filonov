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

"""Defines fetching data from a file."""

import os
from collections.abc import Sequence
from typing import Literal

import pandas as pd
import pydantic
import smart_open
from garf_core import report
from media_tagging import media

from media_fetching import exceptions
from media_fetching.sources import models


class FileFetchingParameters(models.FetchingParameters):
  """File specific parameters for getting media."""

  path: os.PathLike[str] | str
  media_type: Literal[tuple(media.MediaTypeEnum.options())] | None = None
  media_identifier: str = 'media_url'
  media_name: str = 'media_name'
  metrics: Sequence[str] | str = ('clicks', 'impressions')
  segments: Sequence[str] | str | None = None
  extra_info: Sequence[str] | None = pydantic.Field(default_factory=list)

  def model_post_init(self, __context__):
    if isinstance(self.metrics, str):
      self.metrics = self.metrics.split(',')
    if isinstance(self.segments, str):
      self.segments = self.segments.split(',')


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts information from a file to a media report."""

  def fetch_media_data(
    self,
    fetching_request: FileFetchingParameters,
  ) -> report.GarfReport:
    raw_report = report.GarfReport.from_pandas(
      pd.read_csv(smart_open.open(fetching_request.path))
    )
    if (
      media_url := fetching_request.media_identifier
    ) not in raw_report.column_names:
      raise exceptions.MediaFetchingError(
        f'media_url {media_url} not found in the file'
      )
    if (
      media_name := fetching_request.media_identifier
    ) not in raw_report.column_names:
      raise exceptions.MediaFetchingError(
        f'media_name {media_name} not found in the file'
      )
    for row in raw_report:
      row['media_url'] = row[media_url]
      row['media_name'] = row[media_name]
    return raw_report
