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

import dataclasses
import functools
import logging
import operator
import os
from collections.abc import Sequence
from typing import Final, Literal

import garf_youtube_data_api
import numpy as np
import pandas as pd
from filonov.inputs import interfaces, queries
from gaarf import api_clients, report, report_fetcher
from media_tagging import media


@dataclasses.dataclass
class FetchingRequest:
  """Specifies parameters of report fetching."""

  media_type: queries.SupportedMediaTypes
  campaign_types: Sequence[queries.SupportedCampaignTypes]
  start_date: str
  end_date: str


@dataclasses.dataclass
class MediaInfoFileInput:
  """Specifies column names in input file."""

  media_identifier: str
  media_name: str
  metric_names: Sequence[str]


_CORE_METRICS: Final[tuple[str, ...]] = (
  'cost',
  'impressions',
  'clicks',
  'conversions',
  'conversions_value',
)


def from_file(
  path: os.PathLike[str],
  media_type: Literal['image', 'youtube_video'],
  with_size_base: str | None = None,
) -> dict[str, interfaces.MediaInfo]:
  """Generates MediaInfo from a file.

  Args:
    path: Path to files with Google Ads performance data.
    media_type: Type of media found in a file.
    with_size_base: Optional metric to calculate size of media in the output.

  Returns:
    File content converted to MediaInfo mapping.

  Raises:
    ValueError: If files doesn't have all required input columns.
  """
  performance = report.GaarfReport.from_pandas(pd.read_csv(path))
  if missing_columns := {'media_url', 'media_name', *_CORE_METRICS}.difference(
    set(performance.column_names)
  ):
    raise ValueError(f'Missing column(s) in {path}: {missing_columns}')
  return _convert_to_media_info(performance, media_type, with_size_base)


class ExtraInfoFetcher:
  """Extracts additional information from Google Ads to build CreativeMap."""

  def __init__(
    self, accounts: str | Sequence[str], ads_config: os.PathLike[str] | str
  ) -> None:
    """Initializes ExtraInfoFetcher."""
    self.accounts = accounts
    self.ads_config = ads_config

  def generate_extra_info(
    self, fetching_request: FetchingRequest, with_size_base: str | None = None
  ) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from Ads API and converts to MediaInfo objects."""
    fetcher = report_fetcher.AdsReportFetcher(
      api_client=api_clients.GoogleAdsApiClient(path_to_config=self.ads_config)
    )

    performance_queries = self._define_performance_queries(fetching_request)
    customer_ids = self._define_customer_ids(fetcher, fetching_request)
    performance = self._execute_performance_queries(
      fetcher, performance_queries, fetching_request, customer_ids
    )
    if fetching_request.media_type == 'YOUTUBE_VIDEO':
      video_ids = performance['media_url'].to_list(flatten=True, distinct=True)
      video_extra_info = self._build_youtube_video_extra_info(
        fetcher, customer_ids, video_ids
      )
    else:
      video_extra_info = {}
    self._inject_extra_info_into_reports(
      performance,
      video_extra_info,
      columns=('media_size', 'aspect_ratio'),
    )
    return _convert_to_media_info(
      performance, fetching_request.media_type, with_size_base
    )

  def _define_performance_queries(
    self, fetching_request: FetchingRequest
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
    fetcher: report_fetcher.AdsReportFetcher,
    fetching_request: FetchingRequest,
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
    return fetcher.expand_mcc(self.accounts, customer_ids_query)

  def _execute_performance_queries(
    self,
    fetcher: report_fetcher.AdsReportFetcher,
    performance_queries: Sequence[queries.PerformanceQuery],
    fetching_request: FetchingRequest,
    customer_ids: Sequence[str],
  ) -> report.GaarfReport:
    """Executes performance queries for a set of customer ids.

    If two or more performance queries are specified only common fields are
    included into the resulting report.

    Args:
      fetcher: Instantiated AdsReportFetcher.
      performance_queries: Queries that need to be executed.
      fetching_request: Request for fetching data from Google Ads.
      customer_ids: Accounts to get data from.

    Returns:
      Report with media performance.
    """
    performance_reports = []
    common_fields = list(queries.PerformanceQuery.required_fields)
    for campaign_type, query in performance_queries.items():
      fetching_parameters = dataclasses.asdict(fetching_request)
      fetching_parameters.pop('campaign_types')
      fetching_parameters['campaign_type'] = campaign_type
      performance = fetcher.fetch(
        query(**fetching_parameters),
        customer_ids,
      )
      if len(performance_queries) > 1:
        performance_reports.append(performance[common_fields])
      else:
        return performance
    return functools.reduce(operator.add, performance_reports)

  def _build_youtube_video_extra_info(
    self,
    fetcher: report_fetcher.AdsReportFetcher,
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

    video_orientations = video_orientations.to_dict(
      key_column='id',
      value_column='aspect_ratio',
      value_column_output='scalar',
    )
    video_extra_info = {}
    for video_id, aspect_ratio in video_orientations.items():
      video_extra_info[video_id] = {'aspect_ratio': aspect_ratio}
      video_extra_info[video_id].update(
        {'media_size': video_durations.get(video_id)}
      )
    return video_extra_info

  def _inject_extra_info_into_reports(
    self,
    performance_report: report.GaarfReport,
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
      if row.aspect_ratio > 1:
        row['orientation'] = 'Landscape'
      elif row.aspect_ratio < 1:
        row['orientation'] = 'Portrait'
      else:
        row['orientation'] = 'Square'


def _convert_to_media_info(
  performance: report.GaarfReport,
  media_type: queries.SupportedMediaTypes,
  with_size_base: str | None,
) -> dict[str, interfaces.MediaInfo]:
  """Convert report to MediaInfo mappings."""
  if with_size_base and with_size_base not in performance.column_names:
    logging.warning('Failed to set MediaInfo size to {with_size_base}')
    with_size_base = None
  if with_size_base:
    try:
      float(performance[0][with_size_base])
    except TypeError:
      logging.warning('MediaInfo size attribute should be numeric')
      with_size_base = None

  performance = performance.to_dict(key_column='media_url')
  results = {}
  for media_url, values in performance.items():
    info = interfaces.build_info(values, _CORE_METRICS)
    segments = interfaces.build_info(values, ('campaign_type',))
    info.update(
      {
        'orientation': values[0].get('orientation'),
        'media_size': values[0].get('media_size'),
      }
    )
    if values[0].get('date'):
      series = {
        entry.get('date'): interfaces.build_info(entry, _CORE_METRICS)
        for entry in values
      }
    else:
      series = {}
    if with_size_base and (size_base := info.get(with_size_base)):
      media_size = np.log(size_base) * np.log10(size_base)
    else:
      media_size = None
    results[media.convert_path_to_media_name(media_url)] = interfaces.MediaInfo(
      **interfaces.create_node_links(media_url, media_type),
      media_name=values[0].get('media_name'),
      info=info,
      series=series,
      size=media_size,
      segments=segments,
    )
  return results
