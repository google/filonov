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
"""Defines fetching data from Bid Manager API."""

from collections.abc import Sequence

import garf_bid_manager
import pydantic
from garf_core import report

from media_fetching.sources import models


class BidManagerFetchingParameters(models.FetchingParameters):
  """YouTube specific parameters for getting media data."""

  advertiser: str
  metrics: Sequence[str] = [
    'clicks',
    'impressions',
  ]
  segments: Sequence[str] | None = pydantic.Field(default_factory=list)
  extra_info: Sequence[str] | None = pydantic.Field(default_factory=list)


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts media information from Bid Manager API."""

  def fetch_media_data(
    self,
    fetching_request: BidManagerFetchingParameters,
  ) -> report.GarfReport:
    """Fetches performance data from Bid Manager API."""
    fetcher = garf_bid_manager.BidManagerApiReportFetcher()
    query = """
      SELECT
        date AS date,
        youtube_ad_video_id AS media_url,
        youtube_ad_video AS media_name,
        metric_impressions AS impressions,
        metric_clicks AS clicks
      FROM youtube
      WHERE advertiser = {advertiser}
      AND dataRange = LAST_30_DAYS
    """
    return fetcher.fetch(query.format(advertiser=fetching_request.advertiser))
