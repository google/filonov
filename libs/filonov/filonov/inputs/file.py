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

import gaarf
import pandas as pd
import pydantic
from filonov.inputs import interfaces
from media_tagging import media


class FileInputParameters(pydantic.BaseModel):
  """Google Ads specific parameters for generating creative map."""

  model_config = pydantic.ConfigDict(extra='ignore')

  path: os.PathLike[str]
  media_identifier: str
  media_name: str
  metric_names: Sequence[str]


class ExtraInfoFetcher:
  """Extracts additional information from a file to build CreativeMap."""

  def generate_extra_info(
    self,
    fetching_request: FileInputParameters,
    media_type: Literal['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO'],
    with_size_base: str | None = None,
  ) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from Ads API and converts to MediaInfo objects."""
    performance = gaarf.GaarfReport.from_pandas(
      pd.read_csv(fetching_request.path)
    )
    if missing_columns := {'media_url'}.difference(
      set(performance.column_names)
    ):
      raise interfaces.FilonovInputError(
        f'Missing column(s) in {fetching_request.path}: {missing_columns}'
      )
    return interfaces.convert_gaarf_report_to_media_info(
      performance=performance,
      media_type=media.MediaTypeEnum[media_type.upper()],
      with_size_base=with_size_base,
      metric_columns=fetching_request.metric_names,
    )
