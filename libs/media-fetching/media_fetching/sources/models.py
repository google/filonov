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

"""Models and interfaces for media fetching library."""

import abc
import enum

import pydantic
from garf_core import report


class InputSource(str, enum.Enum):
  """Specifies supported sources for getting media performance."""

  googleads = 'googleads'
  youtube = 'youtube'
  file = 'file'
  bq = 'bq'
  sqldb = 'sqldb'
  fake = 'fake'
  dbm = 'dbm'


class FetchingParameters(pydantic.BaseModel):
  """Interface for parameters for getting media data."""

  model_config = pydantic.ConfigDict(extra='allow')


class BaseMediaInfoFetcher(abc.ABC):
  """Interface for getting data from a source."""

  def __init__(self, **kwargs: str):
    self.kwargs = kwargs

  @abc.abstractmethod
  def fetch_media_data(
    self,
    fetching_request: FetchingParameters,
  ) -> report.GarfReport:
    """Extracts data from a source as a report."""
