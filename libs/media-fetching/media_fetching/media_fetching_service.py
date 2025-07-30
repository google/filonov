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

import logging
from typing import Any, get_args

from garf_core import report

from media_fetching import exceptions
from media_fetching.enrichers import enricher
from media_fetching.sources import fetcher, models

logger = logging.getLogger('media-fetching')


class MediaFetchingService:
  """Extracts media information from a specified source."""

  def __init__(
    self,
    source: models.InputSource = 'googleads',
  ) -> None:
    """Initializes MediaFetchingService."""
    if not (source_fetcher := fetcher.FETCHERS.get(source)):
      raise exceptions.MediaFetchingError(
        f'Incorrect source: {source}. Only {get_args(models.InputSource)} '
        'are supported.'
      )
    self.fetcher = source_fetcher[1]
    self.source = source

  def fetch(
    self,
    request: models.FetchingParameters,
    extra_parameters: dict[str, dict[str, Any]] | None = None,
  ) -> report.GarfReport:
    """Extracts data from specified source."""
    logger.info(
      "Fetching data from source '%s' with parameters: %s",
      self.source,
      request,
    )
    media_data = self.fetcher().fetch_media_data(request)
    if extra_info_modules := request.extra_info:
      extra_data = enricher.prepare_extra_info(
        performance=media_data,
        media_type=request.media_type,
        modules=extra_info_modules,
        params=extra_parameters,
      )
      enricher.enrich(media_data, extra_data)
    return media_data
