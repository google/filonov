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
import functools
from collections.abc import Sequence
from typing import Literal

import pydantic
from garf.community.google.bid_manager import BidManagerApiReportFetcher
from garf.community.google.youtube import YouTubeDataApiReportFetcher
from garf.core import report

from media_fetching import exceptions
from media_fetching.sources import models


class BidManagerFetchingParameters(models.FetchingParameters):
  """YouTube specific parameters for getting media data."""

  advertiser: str
  campaigns: list[str] | str = pydantic.Field(default_factory=list)
  line_item_type: str | None = None
  country: str | None = None
  metrics: Sequence[str] | str = [
    'clicks',
    'impressions',
    'cost',
  ]
  media_type: Literal['YOUTUBE_VIDEO'] = 'YOUTUBE_VIDEO'
  start_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=30)
  ).strftime('%Y-%m-%d')
  end_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=1)
  ).strftime('%Y-%m-%d')
  segments: str | list[str] | None = pydantic.Field(default_factory=list)
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
    metrics = []
    for metric in self.metrics:
      if metric.startswith('brand_lift'):
        continue
      if metric == 'cost':
        metrics.append('metric_client_cost_advertiser_currency AS cost')
      else:
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
      'line_item_type': line_item_type,
      'start_date': self.start_date,
      'end_date': self.end_date,
      'metrics': ', '.join(metrics),
    }


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts media information from Bid Manager API."""

  def __init__(self, enable_cache: bool = False, **kwargs) -> None:
    self.enable_cache = enable_cache
    self._fetcher = None

  @property
  def fetcher(self) -> BidManagerApiReportFetcher:
    if not self._fetcher:
      self._fetcher = BidManagerApiReportFetcher(enable_cache=self.enable_cache)
    return self._fetcher

  def fetch_media_data(
    self,
    fetching_request: BidManagerFetchingParameters,
  ) -> report.GarfReport:
    """Fetches performance data from Bid Manager API."""
    line_items = set()
    intersected_line_items = []
    if country := fetching_request.country:
      country_line_item_ids = self._get_country_line_items(
        fetching_request, country
      )
      if not country_line_item_ids:
        raise exceptions.MediaFetchingError(
          f'No line items found for  country {country}'
        )
      line_items = line_items.union(country_line_item_ids)
      intersected_line_items.append(country_line_item_ids)

    if fetching_request.campaigns:
      campaign_line_items = self._get_campaign_line_items(fetching_request)
      if not campaign_line_items:
        raise exceptions.MediaFetchingError(
          f'No line items found for campaigns: {fetching_request.campaigns}'
        )
      line_items = line_items.union(campaign_line_items)
      intersected_line_items.append(campaign_line_items)

    if not line_items:
      line_items = ''
    else:
      line_items = functools.reduce(set.intersection, intersected_line_items)
      if not line_items:
        raise exceptions.MediaFetchingError('No line items found')
      ids = ', '.join(str(line_item) for line_item in line_items)
      line_items = f'AND line_item IN ({ids})'

    query = """
      SELECT
        date AS date,
        trueview_ad_group_id AS ad_group_id,
        youtube_ad_video_id AS media_url,
        youtube_ad_video AS media_name,
        video_duration AS duration,
        advertiser_currency AS _,
        {metrics}
      FROM youtube
      WHERE advertiser IN ({advertiser})
      {line_item_type}
      {line_items}
      AND dataRange IN ({start_date}, {end_date})
    """
    performance = self.fetcher.fetch(
      query.format(**fetching_request.query_parameters, line_items=line_items)
    )
    if fetching_request.media_type == 'YOUTUBE_VIDEO':
      self._add_video_info(performance)
    return performance

  def _get_line_items_with_country(
    self,
    fetching_request: BidManagerFetchingParameters,
    country: str,
  ) -> set[str]:
    """Fetches line items targeting specific countries."""
    query = """
        SELECT
          line_item,
          metric_impressions AS _
        FROM standard
        WHERE advertiser IN ({advertiser})
        AND country IN ({country})
        AND dataRange IN ({start_date}, {end_date})
      """
    line_items = self.fetcher.fetch(
      query.format(**fetching_request.query_parameters, country=country)
    ).to_list(row_type='scalar', distinct=True)
    return set(line_items)

  def _get_country_line_items(
    self,
    fetching_request: BidManagerFetchingParameters,
    country: str,
  ) -> set[str]:
    """Fetches line items for a specific set of countries."""
    threshold = 0.5

    line_items_ids = self._get_line_items_with_country(
      fetching_request, country
    )
    line_item_ids = ', '.join(str(line_item) for line_item in line_items_ids)

    def get_dominant_country(group):
      dominant_country_row = group[group['share'] > threshold]
      if dominant_country_row.empty:
        return 'Unknown'
      return dominant_country_row['target_country'].iloc[0]

    query = """
        SELECT
          line_item,
          country,
          advertiser_currency AS _,
          metric_client_cost_advertiser_currency AS cost
        FROM standard
        WHERE advertiser IN ({advertiser})
        AND line_item IN ({line_item_ids})
        AND dataRange IN ({start_date}, {end_date})
      """
    line_items = self.fetcher.fetch(
      query.format(
        **fetching_request.query_parameters,
        country=country,
        line_item_ids=line_item_ids,
      )
    )
    countries = country.split(',')
    for row in line_items:
      row['target_country'] = row.country in countries
    line_items = line_items.to_pandas()

    line_items['country'] = line_items['country'].fillna('Unknown')
    line_items['total_campaign_cost'] = line_items.groupby('line_item')[
      'cost'
    ].transform('sum')
    line_items['share'] = line_items['cost'] / line_items['total_campaign_cost']
    geo_info = (
      line_items.groupby('line_item').apply(get_dominant_country).to_dict()
    )
    return {
      line_item
      for line_item, country in geo_info.items()
      if country != 'Unknown'
    }

  def _get_campaign_line_items(
    self,
    fetching_request: BidManagerFetchingParameters,
  ) -> set[str]:
    """Fetches line items for a specific set of campaigns."""
    campaigns = ', '.join(
      campaign.strip() for campaign in fetching_request.campaigns
    )
    query = """
        SELECT
          line_item,
          metric_impressions AS _
        FROM standard
        WHERE advertiser IN ({advertiser})
        AND media_plan_name IN ({campaigns})
        AND dataRange IN ({start_date}, {end_date})
      """
    line_items = self.fetcher.fetch(
      query.format(**fetching_request.query_parameters, campaigns=campaigns)
    ).to_list(row_type='scalar', distinct=True)
    return set(line_items)

  def _add_video_info(
    self,
    performance: report.GarfReport,
  ) -> None:
    """Injects YouTube specific information on media.

    Args:
      performance: Report to add video data into.

    Returns:
      Mapping between video id and its information.
    """
    video_orientations_query = """
    SELECT
      id,
      player.embedWidth AS width,
      player.embedHeight AS height
    FROM videos
    """

    video_ids = performance['media_url'].to_list(
      row_type='scalar', distinct=True
    )
    youtube_api_fetcher = YouTubeDataApiReportFetcher()
    video_orientations = youtube_api_fetcher.fetch(
      video_orientations_query,
      id=video_ids,
      maxWidth=500,
    )

    for row in video_orientations:
      aspect_ratio = round(int(row.width) / int(row.height), 2)
      if aspect_ratio > 1:
        row['orientation'] = 'Landscape'
      elif aspect_ratio < 1:
        row['orientation'] = 'Portrait'
      else:
        row['orientation'] = 'Square'

    video_orientations = video_orientations.to_dict(
      key_column='id',
      value_column='orientation',
      value_column_output='scalar',
    )
    for row in performance:
      video_id = row.media_url
      duration = round(int(row.duration) / 1e3)
      row.duration = duration
      row.duration = duration
      row['orientation'] = video_orientations.get(video_id, 0.0)
