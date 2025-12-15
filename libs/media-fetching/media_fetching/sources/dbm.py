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
from typing import Literal

import garf_bid_manager
import pydantic
from garf_core import report

from media_fetching.sources import models


class BidManagerFetchingParameters(models.FetchingParameters):
  """YouTube specific parameters for getting media data."""

  advertiser: str
  campaigns: list[str] | str | None = None
  line_item_type: str | None = None
  country: str | None = None
  metrics: Sequence[str] | str = [
    'clicks',
    'impressions',
  ]
  media_type: Literal['YOUTUBE_VIDEO'] = 'YOUTUBE_VIDEO'
  start_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=30)
  ).strftime('%Y-%m-%d')
  end_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=1)
  ).strftime('%Y-%m-%d')
  segments: list[str] | str | None = pydantic.Field(default_factory=list)
  extra_info: str | list[str] | None = pydantic.Field(default_factory=list)

  def model_post_init(self, __context__) -> None:
    if isinstance(self.metrics, str):
      self.metrics = self.metrics.split(',')
    if isinstance(self.segments, str):
      self.segments = self.segments.split(',')
    if isinstance(self.campaigns, str):
      self.campaigns = self.campaigns.split(',')
    if isinstance(self.extra_info, str):
      self.extra_info = self.extra_info.split(',')

  @property
  def query_parameters(self) -> dict[str, str]:
    if self.campaigns:
      campaigns = ', '.join(campaign.strip() for campaign in self.campaigns)
      campaigns = f'AND campaign IN ({campaigns})'
    else:
      campaigns = ''
    metrics = []
    for metric in self.metrics:
      if metric.startswith('brand_lift'):
        continue
      metrics.append(f'metric_{metric} AS {metric}')
    if self.line_item_type:
      line_item_types = ', '.join(
        line_item.strip() for line_item in self.line_item_type.split(',')
      )
      line_item_type = f'AND line_item_type IN ({line_item_types})'
    else:
      line_item_type = ''
    return {
      'advertiser': ','.join(
        advertiser.strip() for advertiser in self.advertiser.split(',')
      ),
      'campaigns': campaigns,
      'line_item_type': line_item_type,
      'start_date': self.start_date,
      'end_date': self.end_date,
      'metrics': ', '.join(metrics),
    }


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts media information from Bid Manager API."""

  def __init__(self, enable_cache: bool = False) -> None:
    self.enable_cache = enable_cache
    self._fetcher = None

  @property
  def fetcher(self) -> garf_bid_manager.BidManagerApiReportFetcher:
    if not self._fetcher:
      self._fetcher = garf_bid_manager.BidManagerApiReportFetcher(
        enable_cache=self.enable_cache
      )
    return self._fetcher

  def fetch_media_data(
    self,
    fetching_request: BidManagerFetchingParameters,
  ) -> report.GarfReport:
    """Fetches performance data from Bid Manager API."""
    if country := fetching_request.country:
      if line_item_ids := self._get_line_items(fetching_request, country):
        ids = ', '.join(str(line_item) for line_item in line_item_ids)
        line_items = f'AND line_item IN ({ids})'
      else:
        line_items = ''
    else:
      line_items = ''
    query = """
      SELECT
        date AS date,
        trueview_ad_group_id AS ad_group_id,
        youtube_ad_video_id AS media_url,
        youtube_ad_video AS media_name,
        video_duration AS video_duration,
        {metrics}
      FROM youtube
      WHERE advertiser IN ({advertiser})
      {line_item_type}
      {line_items}
      {campaigns}
      AND dataRange IN ({start_date}, {end_date})
    """
    return self.fetcher.fetch(
      query.format(**fetching_request.query_parameters, line_items=line_items)
    )

  def _get_line_items(
    self,
    fetching_request: BidManagerFetchingParameters,
    country: str,
  ) -> list[str]:
    """Fetches line items for a specific set of countries."""
    query = """
        SELECT
          line_item,
          metric_impressions
        FROM standard
        WHERE advertiser IN ({advertiser})
        AND country IN ({country})
        AND dataRange IN ({start_date}, {end_date})
      """
    return self.fetcher.fetch(
      query.format(**fetching_request.query_parameters, country=country)
    ).to_list(row_type='scalar', distinct=True)
