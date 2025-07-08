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

"""Responsible for fetching media specific information from various sources."""

from collections.abc import Sequence
from typing import Literal, get_args

from garf_core import report

from media_fetching import exceptions
from media_fetching.enrichers import enricher
from media_fetching.sources import fetcher

InputSource = Literal['googleads', 'youtube', 'file']


class MediaFetcherService:
  """Extracts media information from a specified source."""

  def __init__(
    self,
    source: InputSource = 'googleads',
  ) -> None:
    """Initializes MediaFetcherService."""
    if source not in get_args(InputSource):
      raise exceptions.MediaFetchingError(
        f'Incorrect source: {source}. Only {get_args(InputSource)} '
        'are supported.'
      )
    self.source = source

  def fetch(
    self,
    media_type: str,
    input_parameters: dict[str, str],
  ) -> report.GarfReport:
    """Extracts data from specified source.

    Args:
      media_type: Type of media to get.
      input_parameters: Parameters to fine-tune fetching.

    Returns:
      Report with fetched data.
    """
    source_fetcher, fetching_request = fetcher.build_fetching_context(
      self.source, media_type, input_parameters
    )
    return source_fetcher.fetch_media_data(fetching_request)

  def enrich(
    self,
    performance: report.GarfReport,
    media_type: str,
    modules: Sequence[str],
    params: dict[str, dict[str, str]],
  ) -> None:
    """Inject extra information into report.

    Args:
      performance: Report with performance data.
      media_type:  Type of media in the report.
      modules: Modules used to perform enriching.
      params: Parameters to perform enriching.
    """
    extra_data = enricher.prepare_extra_info(
      performance, media_type, modules, params
    )
    enricher.enrich(performance, extra_data)
