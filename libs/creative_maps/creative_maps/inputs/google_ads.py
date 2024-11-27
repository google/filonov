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
import operator
import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Literal

import garf_youtube_data_api
import pandas as pd
from creative_maps.inputs import interfaces, queries
from gaarf import api_clients, report_fetcher
from media_tagging import media


@dataclasses.dataclass
class FetchingRequest:
  """Specifies parameters of report fetching."""

  media_type: queries.SupportedMediaTypes
  campaign_type: queries.SupportedCampaignTypes
  start_date: str
  end_date: str


@dataclasses.dataclass
class MediaInfoFileInput:
  """Specifies column names in input file."""

  media_identifier: str
  media_name: str
  metric_names: Sequence[str]


def from_file(
  path: os.PathLike[str],
  file_column_input: MediaInfoFileInput,
  media_type: Literal['image', 'youtube_video'],
) -> dict[str, interfaces.MediaInfo]:
  """Generates MediaInfo from a file.

  Args:
    path: Path to files with Google Ads performance data.
    file_column_input: Identifiers for MediaInfo results.
    media_type: Type of media found in a file.

  Returns:
    File content converted to MediaInfo mapping.

  Raises:
    ValueError: If file doesn't have all required input columns.
  """
  media_identifier, media_name, metrics = (
    file_column_input.media_identifier,
    file_column_input.media_name,
    file_column_input.metric_names,
  )
  data = pd.read_csv(path)
  if missing_columns := {media_name, *metrics}.difference(set(data.columns)):
    raise ValueError(f'Missing column(s) in {path}: {missing_columns}')
  data['info'] = data.apply(
    lambda row: {metric: row[metric] for metric in metrics},
    axis=1,
  )
  grouped = (
    data.groupby([media_name, media_identifier]).info.apply(list).reset_index()
  )
  results = {}
  for _, row in grouped.iterrows():
    info = defaultdict(float)
    for element in row['info']:
      for metric in metrics:
        info[metric] += element.get(metric)
    results[row[media_identifier]] = interfaces.MediaInfo(
      **_create_node_links(row[media_identifier], media_type),
      media_name=row[media_name],
      info=info,
      series={},
    )
  return results


class ExtraInfoFetcher:
  """Extracts additional information from Google Ads to build CreativeMap."""

  def __init__(
    self, accounts: str | Sequence[str], ads_config: os.PathLike[str] | str
  ) -> None:
    """Initializes ExtraInfoFetcher."""
    self.accounts = accounts
    self.ads_config = ads_config

  def generate_extra_info(
    self,
    fetching_request: FetchingRequest,
  ) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from Ads API and converts to MediaInfo objects."""
    fetcher = report_fetcher.AdsReportFetcher(
      api_client=api_clients.GoogleAdsApiClient(path_to_config=self.ads_config)
    )
    youtube_api_fetcher = garf_youtube_data_api.YouTubeDataApiReportFetcher()
    core_metrics = (
      'cost',
      'impressions',
      'clicks',
      'conversions',
      'conversions_value',
    )

    query = queries.QUERIES_MAPPING.get(fetching_request.campaign_type)
    if fetching_request.campaign_type == 'demandgen':
      query = query.get(fetching_request.media_type)
    campaign_types = queries.CAMPAIGN_TYPES_MAPPING.get(
      fetching_request.campaign_type
    )
    customer_ids_query = (
      'SELECT customer.id FROM campaign '
      f'WHERE campaign.advertising_channel_type IN ({campaign_types})'
    )
    customer_ids = fetcher.expand_mcc(self.accounts, customer_ids_query)
    performance = fetcher.fetch(
      query(**dataclasses.asdict(fetching_request)),
      customer_ids,
    )
    if fetching_request.media_type == 'YOUTUBE_VIDEO':
      video_durations = fetcher.fetch(
        queries.YouTubeVideoDurations(), customer_ids
      ).to_dict(
        key_column='video_id',
        value_column='video_duration',
        value_column_output='scalar',
      )
      video_orientations = youtube_api_fetcher.fetch(
        queries.YOUTUBE_VIDEO_ORIENTATIONS_QUERY,
        id=performance['media_url'].to_list(flatten=True, distinct=True),
        maxWidth=500,
      )

      for row in video_orientations:
        row['aspect_ratio'] = round(int(row.width) / int(row.height), 2)

      video_orientations = video_orientations.to_dict(
        key_column='id',
        value_column='aspect_ratio',
        value_column_output='scalar',
      )
      for row in performance:
        row['media_size'] = video_durations.get(row.media_url, 0)
        row['aspect_ratio'] = video_orientations.get(row.media_url, 0)
    for row in performance:
      if row.aspect_ratio > 1:
        row['orientation'] = 'Landscape'
      elif row.aspect_ratio < 1:
        row['orientation'] = 'Portrait'
      else:
        row['orientation'] = 'Square'
    performance = performance.to_dict(key_column='media_url')
    results = {}
    media_type = fetching_request.media_type
    for media_url, values in performance.items():
      info = _build_info(values, core_metrics)
      info.update(
        {'orientation': row.orientation, 'media_size': row.media_size}
      )
      if values[0].get('date'):
        series = {
          entry.get('date'): _build_info(entry, core_metrics)
          for entry in values
        }
      else:
        series = {}
      results[media.convert_path_to_media_name(media_url)] = (
        interfaces.MediaInfo(
          **_create_node_links(media_url, media_type),
          media_name=values[0].get('asset_id'),
          info=info,
          series=series,
        )
      )
    return results


def _sum_nested_metric(
  metric_name: str, data: Mapping[str, float] | Sequence[Mapping[str, float]]
) -> float | int:
  get_metric_getter = operator.itemgetter(metric_name)
  if isinstance(data, Mapping):
    return get_metric_getter(data)
  return sum(map(get_metric_getter, data))


def _build_info(data, core_metrics) -> dict[str, float | int]:
  return {metric: _sum_nested_metric(metric, data) for metric in core_metrics}


def _create_node_links(url: str, media_type: str) -> dict[str, str]:
  return {
    'media_path': _to_youtube_video_link(url)
    if media_type.lower() == 'youtube_video'
    else url,
    'media_preview': _to_youtube_preview_link(url)
    if media_type.lower() == 'youtube_video'
    else url,
  }


def _to_youtube_preview_link(video_id: str) -> str:
  return f'https://img.youtube.com/vi/{video_id}/0.jpg'


def _to_youtube_video_link(video_id: str) -> str:
  return f'https://www.youtube.com/watch?v={video_id}'
