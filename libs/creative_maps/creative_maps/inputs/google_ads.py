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

import pandas as pd
from creative_maps.inputs import interfaces
from gaarf import api_clients, base_query, report_fetcher
from media_tagging import media

SupportedMediaTypes = Literal['IMAGE', 'YOUTUBE_VIDEO']


@dataclasses.dataclass
class ImageLinks(base_query.BaseQuery):
  """Fetches image urls."""

  query_text = """
   SELECT
     asset.id AS asset_id,
     asset.image_asset.full_size.url AS media_url
   FROM asset
   WHERE asset.type = IMAGE
  """


@dataclasses.dataclass
class YouTubeLinks(base_query.BaseQuery):
  """Fetches YouTube links."""

  query_text = """
   SELECT
     asset.id AS asset_id,
     asset.youtube_video_asset.youtube_video_id AS media_url
   FROM asset
   WHERE asset.type = YOUTUBE_VIDEO
  """


@dataclasses.dataclass
class AppAssetPerformance(base_query.BaseQuery):
  """Fetches performance for app campaigns."""

  query_text = """
  SELECT
    segments.date AS date,
    asset.id AS asset_id,
    asset.name AS asset_name,
    {media_url} AS media_url,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.biddable_app_install_conversions AS installs,
    metrics.biddable_app_post_install_conversions AS inapps
  FROM ad_group_ad_asset_view
  WHERE
    asset.type = {media_type}
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  min_cost: int = 0

  def __post_init__(self) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    if self.media_type == 'IMAGE':
      self.media_url = 'asset.image_asset.full_size.url'
    else:
      self.media_url = 'asset.youtube_video_asset.youtube_video_id'


@dataclasses.dataclass
class FetchingRequest:
  """Specifies parameters of report fetching."""

  media_type: SupportedMediaTypes
  start_date: str
  end_date: str


@dataclasses.dataclass
class MediaInfoFileInput:
  """Specifies column names in input file."""

  media_identifier: str
  media_name: str
  media_path_name: str
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
  media_identifier, media_name, media_path, metrics = (
    file_column_input.media_identifier,
    file_column_input.media_name,
    file_column_input.media_path_name,
    file_column_input.metric_names,
  )
  data = pd.read_csv(path)
  if missing_columns := {media_name, media_path, *metrics}.difference(
    set(data.columns)
  ):
    raise ValueError(f'Missing column(s) in {path}: {missing_columns}')
  data['media_path'] = data.apply(
    lambda row: f'https://img.youtube.com/vi/{row[media_path]}/0.jpg'
    if media_type == 'youtube_video'
    else row[media_path],
    axis=1,
  )
  data['info'] = data.apply(
    lambda row: {metric: row[metric] for metric in metrics},
    axis=1,
  )
  grouped = (
    data.groupby([media_name, media_path]).info.apply(list).reset_index()
  )
  results = {}
  for _, row in grouped.iterrows():
    info = defaultdict(float)
    for element in row['info']:
      for metric in metrics:
        info[metric] += element.get(metric)
    results[row[media_identifier]] = interfaces.MediaInfo(
      media_path=row[media_path],
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
    customer_ids = fetcher.expand_mcc(
      self.accounts,
      customer_ids_query=(
        'SELECT customer.id FROM campaign '
        'WHERE campaign.advertising_channel_type = MULTI_CHANNEL'
      ),
    )
    core_metrics = ('cost', 'impressions', 'clicks', 'inapps')
    asset_performance = fetcher.fetch(
      AppAssetPerformance(**dataclasses.asdict(fetching_request)),
      customer_ids,
    ).to_dict(key_column='media_url')
    results = {}
    for media_url, values in asset_performance.items():
      series = {
        entry.get('date'): _build_info(entry, core_metrics) for entry in values
      }
      results[media.convert_path_to_media_name(media_url)] = (
        interfaces.MediaInfo(
          media_path=media_url,
          media_name=values[0].get('asset_id'),
          info=_build_info(values, core_metrics),
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
