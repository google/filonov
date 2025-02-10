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

from filonov.inputs import google_ads, interfaces, youtube

InputSource = Literal['googleads', 'youtube', 'file']
Context = dict[str, str]


class MediaInputServiceError(Exception):
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

    Raises:
      MediaInputServiceError: When incomplete input parameters are supplied.
    """
    if self.source == 'youtube':
      if not (channel := input_parameters.get('channel')):
        raise MediaInputServiceError(
          'Missing required argument `channel` for source `youtube`'
        )
      context = {'channel': channel}
      return (
        youtube.ExtraInfoFetcher(channel).generate_extra_info(),
        context,
      )
    if self.source == 'file':
      if 'performance_results_path' not in input_parameters:
        raise MediaInputServiceError(
          'Missing required argument `performance_results_path` '
          'for source `file`'
        )
      return (
        google_ads.from_file(
          media_type=media_type,
          path=input_parameters.get('performance_results_path'),
          with_size_base=with_size_base,
        ),
        {},
      )
    if 'ads_config_path' in input_parameters:
      ads_config = input_parameters.pop('ads_config_path')
    if 'account' in input_parameters:
      accounts = input_parameters.pop('account')
    fetcher = google_ads.ExtraInfoFetcher(
      accounts=accounts, ads_config=ads_config
    )
    fetching_request = google_ads.FetchingRequest(
      media_type=media_type,
      **input_parameters,
    )
    context = {**fetching_request.to_dict(), 'account': accounts}
    return (
      fetcher.generate_extra_info(fetching_request, with_size_base),
      context,
    )
