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
"""Modules for building and validating inputs for creative map generation."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import dataclasses
import os
from typing import Any

from media_tagging import tagging_result

from creative_maps.inputs import google_ads


@dataclasses.dataclass
class BaseInputRequest:
  """Base class for input requests."""

  def to_dict(self) -> dict[str, Any]:
    """Converts dataclass isinstance to dictionary."""
    return dataclasses.asdict(self)


@dataclasses.dataclass
class FileInputRequest(BaseInputRequest):
  """Specifies necessary elements for interacting with file mode."""

  tagging_results_path: os.PathLike[str]
  performance_results_path: os.PathLike[str]
  tagging_columns: tagging_result.TaggingResultsFileInput = dataclasses.field(
    default_factory=lambda: tagging_result.TaggingResultsFileInput(
      identifier_name='ytid', tag_name='id', score_name='value'
    )
  )
  performance_columns: google_ads.MediaInfoFileInput = dataclasses.field(
    default_factory=lambda: google_ads.MediaInfoFileInput(
      media_identifier='url',
      media_name='title',
      metric_names=['clicks', 'impressions'],
    ),
  )


@dataclasses.dataclass
class ApiInputRequest(BaseInputRequest):
  """Specifies necessary elements for interacting with API mode."""

  account: str
  start_date: str
  end_date: str
  tagger: str
  ads_config_path: str | os.PathLike[str]
