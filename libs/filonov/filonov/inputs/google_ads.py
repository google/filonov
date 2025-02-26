# Copyright 2024 Google LLC
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

"""Defines imports from Google Ads Reports."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import datetime
import functools
import operator
import pathlib
from collections.abc import Sequence
from typing import Final, get_args

import gaarf
import garf_youtube_data_api
import pydantic
from filonov.inputs import interfaces, queries
from media_tagging import media


class GoogleAdsInputParameters(pydantic.BaseModel):
  """Google Ads specific parameters for generating creative map."""

  model_config = pydantic.ConfigDict(extra='ignore')
  account: str
  start_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=30)
  ).strftime('%Y-%m-%d')
  end_date: str = (
    datetime.datetime.today() - datetime.timedelta(days=1)
  ).strftime('%Y-%m-%d')

  campaign_types: Sequence[queries.SupportedCampaignTypes] | str = ('app',)
  ads_config_path: str = str(pathlib.Path.home() / 'google-ads.yaml')

  def model_post_init(self, __context):  # noqa: D105
    if self.campaign_types == 'all':
      self.campaign_types = get_args(queries.SupportedCampaignTypes)
    elif isinstance(self.campaign_types, str):
      self.campaign_types = self.campaign_types.split(',')


_CORE_METRICS: Final[tuple[str, ...]] = (
  'clicks',
  'impressions',
  'cost',
  'conversions',
  'conversions_value',
)


class ExtraInfoFetcher:
  """Extracts additional information from Google Ads to build CreativeMap."""

  def fetch_media_data(
    self,
    fetching_request: GoogleAdsInputParameters,
    media_type: str,
  ) -> gaarf.GaarfReport:
    """Fetches performance data from Google Ads API."""
    fetcher = gaarf.AdsReportFetcher(
      api_client=gaarf.GoogleAdsApiClient(
        path_to_config=fetching_request.ads_config_path
      )
    )

    performance_queries = self._define_performance_queries(fetching_request)
    customer_ids = self._define_customer_ids(fetcher, fetching_request)
    performance = self._execute_performance_queries(
      fetcher=fetcher,
      performance_queries=performance_queries,
      fetching_request=fetching_request,
      media_type=media_type,
      customer_ids=customer_ids,
    )
    if media_type == 'YOUTUBE_VIDEO':
      video_ids = performance['media_url'].to_list(flatten=True, distinct=True)
      video_extra_info = self._build_youtube_video_extra_info(
        fetcher, customer_ids, video_ids
      )
    else:
      video_extra_info = {}
    media_size_column = (
      'file_size' if media_type == 'IMAGE' else 'video_duration'
    )

    self._inject_extra_info_into_reports(
      performance,
      video_extra_info,
      columns=(media_size_column, 'aspect_ratio'),
    )
    return performance

  def generate_extra_info(
    self,
    fetching_request: GoogleAdsInputParameters,
    media_type: str,
    with_size_base: str | None = None,
  ) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from Ads API and converts to MediaInfo objects."""
    if not (performance := self.fetch_media_data(fetching_request, media_type)):
      return {}
    return interfaces.convert_gaarf_report_to_media_info(
      performance=performance,
      media_type=media.MediaTypeEnum[media_type.upper()],
      metric_columns=_CORE_METRICS,
      segment_columns=('campaign_type',),
      with_size_base=with_size_base,
    )

  def _define_performance_queries(
    self, fetching_request: GoogleAdsInputParameters
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
      if campaign_type == 'demandgen':
        query = query.get(fetching_request.media_type)
      performance_queries[campaign_type] = query
    return performance_queries

  def _define_customer_ids(
    self,
    fetcher: gaarf.AdsReportFetcher,
    fetching_request: GoogleAdsInputParameters,
  ) -> list[str]:
    """Identifies all accounts that have campaigns with specified types.

    Args:
      fetcher: Instantiated AdsReportFetcher.
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
    return fetcher.expand_mcc(fetching_request.account, customer_ids_query)

  def _execute_performance_queries(
    self,
    fetcher: gaarf.AdsReportFetcher,
    performance_queries: dict[str, queries.PerformanceQuery],
    fetching_request: GoogleAdsInputParameters,
    media_type: str,
    customer_ids: Sequence[str],
  ) -> gaarf.GaarfReport:
    """Executes performance queries for a set of customer ids.

    If two or more performance queries are specified only common fields are
    included into the resulting report.

    Args:
      fetcher: Instantiated AdsReportFetcher.
      performance_queries: Queries that need to be executed.
      fetching_request: Request for fetching data from Google Ads.
      media_type: Type of media to fetch.
      customer_ids: Accounts to get data from.

    Returns:
      Report with media performance.
    """
    performance_reports = []
    common_fields = list(queries.PerformanceQuery.required_fields)
    for campaign_type, query in performance_queries.items():
      fetching_parameters = fetching_request.dict()
      fetching_parameters.pop('campaign_types')
      fetching_parameters.pop('account')
      fetching_parameters.pop('ads_config_path')
      fetching_parameters['campaign_type'] = campaign_type
      performance = fetcher.fetch(
        query(media_type=media_type, **fetching_parameters),
        customer_ids,
      )
      if len(performance_queries) > 1:
        performance_reports.append(performance[common_fields])
      else:
        return performance
    return functools.reduce(operator.add, performance_reports)

  def _build_youtube_video_extra_info(
    self,
    fetcher: gaarf.AdsReportFetcher,
    customer_ids: Sequence[str],
    video_ids: Sequence[str],
  ) -> dict[str, dict[str, int]]:
    """Extracts YouTube specific information on media.

    Args:
      fetcher: Instantiated AdsReportFetcher.
      customer_ids: Accounts to get data from.
      video_ids: Videos to get information on.

    Returns:
      Mapping between video id and its information.
    """
    video_durations = {
      video_id: video_lengths[0]
      for video_id, video_lengths in fetcher.fetch(
        queries.YouTubeVideoDurations(), customer_ids
      )
      .to_dict(
        key_column='video_id',
        value_column='video_duration',
      )
      .items()
    }

    youtube_api_fetcher = garf_youtube_data_api.YouTubeDataApiReportFetcher()
    video_orientations = youtube_api_fetcher.fetch(
      queries.YOUTUBE_VIDEO_ORIENTATIONS_QUERY,
      id=video_ids,
      maxWidth=500,
    )

    for row in video_orientations:
      row['aspect_ratio'] = round(int(row.width) / int(row.height), 2)
      if row.aspect_ratio > 1:
        row['orientation'] = 'Landscape'
      elif row.aspect_ratio < 1:
        row['orientation'] = 'Portrait'
      else:
        row['orientation'] = 'Square'

    video_orientations = video_orientations.to_dict(
      key_column='id',
      value_column='aspect_ratio',
      value_column_output='scalar',
    )
    video_extra_info = {}
    for video_id, aspect_ratio in video_orientations.items():
      video_extra_info[video_id] = {'aspect_ratio': aspect_ratio}
      video_extra_info[video_id].update(
        {'video_duration': video_durations.get(video_id)}
      )
    return video_extra_info

  def _inject_extra_info_into_reports(
    self,
    performance_report: gaarf.GaarfReport,
    extra_info: dict[str, dict[str, int]],
    columns: Sequence[str],
    base_key: str = 'media_url',
  ) -> None:
    """Adds additional information to existing performance report.

    Args:
      performance_report: Report with performance data.
      extra_info: Information to be injected into performance report.
      columns: Columns that need to be changed / added to performance report.
      base_key: Common identifier between performance report and extra_info.
    """
    for row in performance_report:
      if extra_info:
        for column in columns:
          row[column] = extra_info.get(row[base_key], {}).get(column)
