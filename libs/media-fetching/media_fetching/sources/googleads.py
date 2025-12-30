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

"""Defines imports from Google Ads Reports."""

import datetime
import functools
import operator
import os
import pathlib
from collections.abc import Mapping, Sequence
from typing import Literal, get_args

import garf_google_ads
import garf_youtube_data_api
import pydantic
from garf_core import report
from media_tagging import media

from media_fetching import exceptions
from media_fetching.sources import models, queries


class GoogleAdsFetchingParameters(models.FetchingParameters):
  """Google Ads specific parameters for getting media data."""

  account: str
  media_type: Literal[tuple(media.MediaTypeEnum.options())] | None = None
  start_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=30)
  ).strftime('%Y-%m-%d')
  end_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=1)
  ).strftime('%Y-%m-%d')
  min_cost: int = 0
  campaign_types: Sequence[queries.SupportedCampaignTypes] | str = ('app',)
  countries: list[str] | str = pydantic.Field(default_factory=list)
  metrics: Sequence[str] | str = [
    'clicks',
    'impressions',
    'cost',
    'conversions',
    'conversions_value',
  ]
  segments: Sequence[str] | str = ('format_type', 'channel_type')
  extra_info: str | Sequence[str] | None = pydantic.Field(default_factory=list)

  def model_post_init(self, __context__):  # noqa: D105
    if self.campaign_types == 'all':
      self.campaign_types = get_args(queries.SupportedCampaignTypes)
    elif isinstance(self.campaign_types, str):
      self.campaign_types = self.campaign_types.split(',')
    if isinstance(self.segments, str):
      self.segments = self.segments.split(',')
    if isinstance(self.countries, str):
      self.countries = self.countries.split(',')
    if isinstance(self.metrics, str):
      self.metrics = self.metrics.split(',')
    if isinstance(self.extra_info, str):
      self.extra_info = self.extra_info.split(',')

  @property
  def query_params(self) -> dict[str, str | int]:
    query_params = {
      'start_date': self.start_date,
      'end_date': self.end_date,
      'media_type': self.media_type,
      'min_cost': self.min_cost,
    }
    query_params.update(self.model_extra)
    return query_params


class Fetcher(models.BaseMediaInfoFetcher):
  """Extracts media information from Google Ads."""

  def __init__(
    self,
    ads_config: str = os.getenv(
      'GOOGLE_ADS_CONFIGURATION_FILE_PATH',
      str(pathlib.Path.home() / 'google-ads.yaml'),
    ),
    enable_cache: bool = False,
    **kwargs: str,
  ) -> None:
    self.ads_config = ads_config
    self.enable_cache = enable_cache
    self._fetcher = None

  @property
  def fetcher(self) -> garf_google_ads.GoogleAdsApiReportFetcher:
    if not self._fetcher:
      self._fetcher = garf_google_ads.GoogleAdsApiReportFetcher(
        api_client=garf_google_ads.api_clients.GoogleAdsApiClient(
          path_to_config=self.ads_config
        ),
        enable_cache=self.enable_cache,
      )
    return self._fetcher

  def fetch_media_data(
    self,
    fetching_request: GoogleAdsFetchingParameters,
  ) -> report.GarfReport:
    """Fetches performance data from Google Ads API.

    Args:
      fetching_request: Request for getting data from Google Ads.

    Returns:
      Report with performance data.

    Raises:
      MediaFetchingError: When there's no data for a given fetching context.

    """
    if isinstance(fetching_request, Mapping):
      fetching_request = GoogleAdsFetchingParameters(**fetching_request)

    performance_queries = self._define_performance_queries(fetching_request)
    self.accounts = self._define_customer_ids(fetching_request)
    performance = self._execute_performance_queries(
      performance_queries=performance_queries,
      fetching_request=fetching_request,
    )
    if not performance:
      raise exceptions.MediaFetchingError(
        f'No performance data found for the context: {fetching_request}'
      )
    self._add_in_campaigns(performance)
    if fetching_request.media_type == 'YOUTUBE_VIDEO':
      self._add_video_info(performance)

    return performance

  def _define_performance_queries(
    self, fetching_request: GoogleAdsFetchingParameters
  ) -> dict[str, queries.PerformanceQuery]:
    """Defines queries based on campaign and media types.

    Args:
      fetching_request: Request for fetching data from Google Ads.

    Returns:
      Mapping between each campaign type and its corresponding query.
    """
    performance_queries = {}
    for campaign_type in fetching_request.campaign_types:
      query = queries.QUERIES_MAPPING.get(campaign_type)
      if (
        campaign_type == 'video' and fetching_request.media_type == 'IMAGE'
      ) or (
        campaign_type == 'search' and fetching_request.media_type != 'TEXT'
      ):
        continue
      if campaign_type == 'demandgen':
        query = query.get(fetching_request.media_type)
      performance_queries[campaign_type] = query
    return performance_queries

  def _define_customer_ids(
    self,
    fetching_request: GoogleAdsFetchingParameters,
  ) -> list[str]:
    """Identifies all accounts that have campaigns with specified types.

    Args:
      fetching_request: Request for fetching data from Google Ads.

    Returns:
      All accounts that have campaigns with specified types.
    """
    campaign_types = ','.join(
      queries.CAMPAIGN_TYPES_MAPPING.get(campaign_type)
      for campaign_type in fetching_request.campaign_types
    )
    customer_ids_query = (
      'SELECT customer.id FROM campaign '
      f'WHERE campaign.advertising_channel_type IN ({campaign_types})'
    )
    return self.fetcher.expand_mcc(fetching_request.account, customer_ids_query)

  def _execute_performance_queries(
    self,
    performance_queries: dict[str, queries.PerformanceQuery],
    fetching_request: GoogleAdsFetchingParameters,
  ) -> report.GarfReport:
    """Executes performance queries for a set of customer ids.

    If two or more performance queries are specified only common fields are
    included into the resulting report.

    Args:
      performance_queries: Queries that need to be executed.
      fetching_request: Request for fetching data from Google Ads.

    Returns:
      Report with media performance.
    """
    performance_reports = []
    if countries := fetching_request.countries:
      campaign_ids = self._get_campaign_ids_for_countries(countries)
      if not campaign_ids:
        raise exceptions.MediaFetchingError(
          'No campaigns with the following dominant countries '
          f'found: {countries}'
        )
    else:
      campaign_ids = []
    for campaign_type, query in performance_queries.items():
      fetching_parameters = fetching_request.query_params
      fetching_parameters['campaign_type'] = campaign_type
      performance = self.fetcher.fetch(
        query_specification=query(
          **fetching_parameters, campaign_ids=campaign_ids
        ),
        account=self.accounts,
      )
      if len(performance_queries) == 1:
        return performance
      if performance:
        performance_reports.append(performance)
    common_fields = []
    for performance_report in performance_reports:
      common_fields.append(set(performance_report.column_names))
    common_fields = list(set.intersection(*common_fields))
    performance_reports = [
      performance_report[common_fields]
      for performance_report in performance_reports
    ]
    return functools.reduce(operator.add, performance_reports)

  def _add_in_campaigns(
    self,
    performance: report.GarfReport,
  ) -> None:
    """Injects number of campaigns media is presented in into report."""
    info = {
      media_url: str(len(campaigns))
      for media_url, campaigns in performance.to_dict(
        'media_url', 'campaign_id'
      ).items()
    }
    for row in performance:
      row['in_campaigns'] = info.get(row.media_url)

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
    video_durations_query = """
     SELECT
       media_file.video.youtube_video_id AS video_id,
       media_file.video.ad_duration_millis / 1000 AS video_duration
     FROM media_file
     WHERE media_file.type = VIDEO
    """
    video_orientations_query = """
    SELECT
      id,
      player.embedWidth AS width,
      player.embedHeight AS height
    FROM videos
    """

    video_durations = {
      video_id: video_lengths[0]
      for video_id, video_lengths in self.fetcher.fetch(
        video_durations_query, self.accounts
      )
      .to_dict(
        key_column='video_id',
        value_column='video_duration',
      )
      .items()
    }

    video_ids = performance['media_url'].to_list(
      row_type='scalar', distinct=True
    )
    youtube_api_fetcher = garf_youtube_data_api.YouTubeDataApiReportFetcher()
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
      row['orientation'] = video_orientations.get(video_id, 0.0)
      row['duration'] = video_durations.get(video_id, 0.0)

  def _get_campaign_ids_for_countries(self, countries: list[str]) -> list[int]:
    threshold = 0.5

    def get_dominant_country(group):
      dominant_country_row = group[group['share'] > threshold]
      if dominant_country_row.empty:
        return 'Unknown'
      return dominant_country_row['country'].iloc[0]

    campaign_geos = """
    SELECT
      campaign.id AS campaign_id,
      user_location_view.country_criterion_id AS country_id,
     metrics.cost_micros / 1e6 AS cost
    FROM user_location_view
    """

    geo_targets_query = """
    SELECT
      geo_target_constant.id AS country_id,
      geo_target_constant.name AS country_name
    FROM geo_target_constant
    WHERE geo_target_constant.id BETWEEN 2000 AND 3000
    """

    country_mapping = self.fetcher.fetch(
      geo_targets_query, self.accounts[0]
    ).to_dict(
      key_column='country_id',
      value_column='country_name',
      value_column_output='scalar',
    )
    geo_extra_info = self.fetcher.fetch(
      campaign_geos, self.accounts
    ).to_pandas()
    geo_extra_info['country'] = geo_extra_info['country_id'].map(
      country_mapping
    )
    geo_extra_info['country'] = geo_extra_info['country'].fillna('Unknown')
    geo_extra_info['total_campaign_cost'] = geo_extra_info.groupby(
      'campaign_id'
    )['cost'].transform('sum')
    geo_extra_info['share'] = (
      geo_extra_info['cost'] / geo_extra_info['total_campaign_cost']
    )
    geo_info = (
      geo_extra_info.groupby('campaign_id')
      .apply(get_dominant_country)
      .to_dict()
    )
    return [
      campaign_id
      for campaign_id, country in geo_info.items()
      if country in countries
    ]
