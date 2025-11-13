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

import datetime
from collections.abc import Sequence

import garf_bid_manager
import pydantic
from garf_core import report

from media_fetching.sources import models


class BidManagerFetchingParameters(models.FetchingParameters):
  """YouTube specific parameters for getting media data."""

  advertiser: str
  line_item_type: str | None = None
  country: str | None = None
  metrics: Sequence[str] = [
    'clicks',
    'impressions',
  ]
  start_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=30)
  ).strftime('%Y-%m-%d')
  end_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=1)
  ).strftime('%Y-%m-%d')
  segments: Sequence[str] | None = pydantic.Field(default_factory=list)
  extra_info: Sequence[str] | None = pydantic.Field(default_factory=list)

  def model_post_init(self, __context__) -> None:
    if self.line_item_type:
      self.line_item_type = f'AND line_item_type = {self.line_item_type}'

  @property
  def query_parameters(self) -> dict[str, str]:
    return {
      'advertiser': self.advertiser,
      'line_item_type': self.line_item_type or '',
      'start_date': self.start_date,
      'end_date': self.end_date,
    }


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts media information from Bid Manager API."""

  def fetch_media_data(
    self,
    fetching_request: BidManagerFetchingParameters,
  ) -> report.GarfReport:
    """Fetches performance data from Bid Manager API."""
    fetcher = garf_bid_manager.BidManagerApiReportFetcher()
    if country := fetching_request.country:
      if line_item_ids := self._get_line_items(
        fetcher, fetching_request.advertiser, country
      ):
        ids = ', '.join(str(line_item) for line_item in line_item_ids)
        line_items = f'AND line_item IN ({ids})'
      else:
        line_items = ''
    else:
      line_items = ''
    query = """
      SELECT
        date AS date,
        youtube_ad_video_id AS media_url,
        youtube_ad_video AS media_name,
        metric_impressions AS impressions,
        metric_clicks AS clicks,
        metric_media_cost_usd AS cost
      FROM youtube
      WHERE advertiser = {advertiser}
      {line_item_type}
      {line_items}
      AND dataRange IN ({start_date}, {end_date})
    """
    return fetcher.fetch(
      query.format(**fetching_request.query_parameters, line_items=line_items)
    )

  def _get_line_items(self, fetcher, advertiser, country) -> list[str]:
    """Fetches performance data from Bid Manager API."""
    query = """
      SELECT
        line_item,
        metric_impressions
      FROM standard
      WHERE advertiser = {advertiser}
      AND country IN ({country})
      AND dataRange = LAST_30_DAYS
    """
    return fetcher.fetch(
      query.format(advertiser=advertiser, country=country)
    ).to_list(row_type='scalar', distinct=True)
