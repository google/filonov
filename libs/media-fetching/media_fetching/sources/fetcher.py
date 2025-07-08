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

"""Instantiates concrete fetcher and builds fetching context."""

from typing import TypeAlias

from media_fetching.sources import file, googleads, models, youtube

MetricInfo: TypeAlias = dict[str, int | float]
Info: TypeAlias = dict[str, int | float | str | list[str]]


def build_fetching_context(
  source: str,
  media_type: str,
  input_parameters: dict[str, str],
) -> tuple[models.BaseMediaInfoFetcher, models.InputParameters]:
  """Builds correct fetching request and initializes appropriate fetcher."""
  if source == 'youtube':
    fetching_request = youtube.YouTubeInputParameters(**input_parameters)
    fetcher = youtube.Fetcher()
  elif source == 'googleads':
    fetching_request = googleads.GoogleAdsInputParameters(**input_parameters)
    fetcher = googleads.Fetcher()
  elif source == 'file':
    fetching_request = file.FileInputParameters(**input_parameters)
    fetcher = file.Fetcher()
  if (
    hasattr(fetching_request, 'media_type') and not fetching_request.media_type
  ):
    fetching_request.media_type = media_type
  return (fetcher, fetching_request)
