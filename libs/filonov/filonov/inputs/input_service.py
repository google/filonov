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

"""Module responsible for extracting media dimensions and metrics."""

from typing import Literal, get_args

from filonov import exceptions
from filonov.inputs import file, google_ads, interfaces, youtube

InputSource = Literal['googleads', 'youtube', 'file']
Context = dict[str, str]


class MediaInputServiceError(exceptions.FilonovError):
  """Base exception for MediaInputService."""


class MediaInputService:
  """Extracts media information from a specified source."""

  def __init__(self, source: InputSource = 'googleads') -> None:
    """Initializes InputService."""
    if source not in get_args(InputSource):
      raise MediaInputServiceError(
        f'Incorrect source: {source}. Only {get_args(InputSource)} '
        'are supported.'
      )
    self.source = source

  def generate_media_info(
    self,
    media_type: str,
    input_parameters: dict[str, str],
    with_size_base: str = 'cost',
  ) -> tuple[dict[str, interfaces.MediaInfo], Context]:
    """Extracts data from service type and converts to MediaInfo objects.

    Args:
      media_type: Type of media to get.
      input_parameters: Parameters to fine-tune fetching.
      with_size_base: Optional metric to calculate size of media in the output.

    Returns:
      Tuple with mapping between media identifiers and media info and a context.
    """
    if self.source == 'youtube':
      fetching_request = youtube.YouTubeInputParameters(**input_parameters)
      fetcher = youtube.ExtraInfoFetcher()
    elif self.source == 'googleads':
      fetching_request = google_ads.GoogleAdsInputParameters(
        media_type=media_type, **input_parameters
      )
      fetcher = google_ads.ExtraInfoFetcher()
    elif self.source == 'file':
      fetching_request = file.FileInputParameters(**input_parameters)
      fetcher = file.ExtraInfoFetcher()
    return (
      fetcher.generate_extra_info(
        fetching_request=fetching_request,
        media_type=media_type,
        with_size_base=with_size_base,
      ),
      fetching_request.dict(),
    )
