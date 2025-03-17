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
"""Defines fetching data from a file."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import os
from collections.abc import Sequence
from typing import Literal

import pandas as pd
import smart_open
from filonov.inputs import interfaces
from garf_core import report
from media_tagging import media


class FileInputParameters(interfaces.InputParameters):
  """File specific parameters for generating creative map."""

  path: os.PathLike[str] | str
  media_type: Literal['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO']
  media_identifier: str = 'media_url'
  media_name: str = 'media_name'
  metric_names: Sequence[str] | str = ('clicks', 'impressions')

  def model_post_init(self, __context):
    if isinstance(self.metric_names, str):
      self.metric_names = self.metric_names.split(',')


class ExtraInfoFetcher(interfaces.BaseMediaInfoFetcher):
  """Extracts additional information from a file to build CreativeMap."""

  def fetch_media_data(
    self,
    fetching_request: FileInputParameters,
  ) -> report.GarfReport:
    return report.GarfReport.from_pandas(
      pd.read_csv(smart_open.open(fetching_request.path))
    )

  def generate_extra_info(
    self,
    fetching_request: FileInputParameters,
    with_size_base: str | None = None,
  ) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from Ads API and converts to MediaInfo objects."""
    performance = self.fetch_media_data(fetching_request)
    if missing_columns := {'media_url'}.difference(
      set(performance.column_names)
    ):
      raise interfaces.FilonovInputError(
        f'Missing column(s) in {fetching_request.path}: {missing_columns}'
      )
    return interfaces.convert_gaarf_report_to_media_info(
      performance=performance,
      media_type=media.MediaTypeEnum[fetching_request.media_type.upper()],
      with_size_base=with_size_base,
      metric_columns=fetching_request.metric_names,
    )
