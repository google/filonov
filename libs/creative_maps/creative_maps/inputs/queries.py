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

"""Contains Google Ads and YouTube Data API queries."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import dataclasses
from typing import Final, Literal

from gaarf import base_query

SupportedMediaTypes = Literal['IMAGE', 'YOUTUBE_VIDEO']
SupportedCampaignTypes = Literal['pmax', 'app', 'demandgen', 'video', 'display']


class PerformanceQuery(base_query.BaseQuery):
  """Enforces presence of certain fields in the query.

  Attributes:
    base_query_text:
      A Gaarf query text template that contains aliases specified
      in `required_fields`.

  Raises:
    ValueError:
      If subclass query_text does not contain all required fields.
  """

  query_text = ''
  required_fields = (
    'date',
    'campaign_type',
    'media_name',
    'media_url',
    'aspect_ratio',
    'media_size',
    'clicks',
    'impressions',
    'cost',
    'conversions',
    'conversions_value',
  )

  def __init_subclass__(cls) -> None:  # noqa: D105
    super().__init_subclass__()
    missing_fields: list[str] = []
    missing_fields = [
      field for field in cls.required_fields if field not in cls.query_text
    ]
    if missing_fields:
      raise ValueError(
        'query_text does not contain required fields: ' f'{missing_fields}'
      )


@dataclasses.dataclass
class YouTubeVideoDurations(base_query.BaseQuery):
  """Fetches YouTube links."""

  query_text = """
   SELECT
     media_file.video.youtube_video_id AS video_id,
     media_file.video.ad_duration_millis / 1000 AS video_duration
   FROM media_file
   WHERE media_file.type = VIDEO
  """


@dataclasses.dataclass
class DisplayAssetPerformance(PerformanceQuery):
  """Fetches image ads performance for Display campaigns."""

  query_text = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.advertising_channel_type AS channel_type,
    ad_group_ad.ad.name AS media_name,
    ad_group_ad.ad.id AS asset_id,
    ad_group_ad.ad.image_ad.image_url AS media_url,
    ad_group_ad.ad.image_ad.pixel_width / ad_group_ad.ad.image_ad.pixel_height
      AS aspect_ratio,
    0 AS media_size,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM ad_group_ad
  WHERE
    ad_group_ad.ad.type = IMAGE_AD
    AND campaign.advertising_channel_type = DISPLAY
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros >= {min_cost}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 10

  def __post_init__(self) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)


@dataclasses.dataclass
class VideoPerformance(PerformanceQuery):
  """Fetches video ad performance for Video campaigns."""

  query_text = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.advertising_channel_type AS channel_type,
    ad_group_ad.ad.type AS ad_type,
    video.id AS media_url,
    video.title AS media_name,
    0 AS aspect_ratio,
    video.duration_millis / 1000 AS media_size,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM video
  WHERE
    campaign.advertising_channel_type = VIDEO
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0

  def __post_init__(self) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)


@dataclasses.dataclass
class PmaxAssetInfo(PerformanceQuery):
  """Fetches asset info for Performance Max campaigns."""

  query_text = """
  SELECT
    '{campaign_type}' AS campaign_type,
    '' AS date,
    campaign.advertising_channel_type AS channel_type,
    asset.id AS asset_id,
    {media_name} AS media_name,
    {media_url} AS media_url,
    {aspect_ratio} AS aspect_ratio,
    {size} AS media_size,
    0 AS cost,
    0 AS clicks,
    0 AS impressions,
    0 AS conversions,
    0 AS conversions_value
  FROM asset_group_asset
  WHERE
    asset.type = {media_type}
    AND campaign.advertising_channel_type = PERFORMANCE_MAX
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0

  def __post_init__(self) -> None:  # noqa: D105
    if self.media_type == 'IMAGE':
      self.media_url = 'asset.image_asset.full_size.url'
      self.aspect_ratio = (
        'asset.image_asset.full_size.width_pixels / '
        'asset.image_asset.full_size.height_pixels'
      )
      self.size = 'asset.image_asset.file_size / 1024'
      self.media_name = 'asset.name'
    else:
      self.media_url = 'asset.youtube_video_asset.youtube_video_id'
      self.aspect_ratio = 0.0
      self.size = 0.0
      self.media_name = 'asset.youtube_video_asset.youtube_video_title'


@dataclasses.dataclass
class DemandGenImageAssetPerformance(PerformanceQuery):
  """Fetches image asset performance for Demand Gen campaigns."""

  query_text = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.advertising_channel_type AS channel_type,
    asset.name AS media_name,
    asset.id AS asset_id,
    asset.image_asset.full_size.url AS media_url,
    asset.image_asset.full_size.width_pixels /
      asset.image_asset.full_size.height_pixels AS aspect_ratio,
    asset.image_asset.file_size / 1024 AS media_size,
    ad_group_ad.ad.name AS ad_name,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM ad_group_ad_asset_view
  WHERE
    campaign.advertising_channel_type =  DEMAND_GEN
    AND asset.type = IMAGE
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0

  def __post_init__(self) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)


@dataclasses.dataclass
class DemandGenVideoAssetPerformance(PerformanceQuery):
  """Fetches video asset performance for Demand Gen campaigns."""

  query_text = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.advertising_channel_type AS channel_type,
    video.id AS media_url,
    video.title AS media_name,
    0 AS aspect_ratio,
    video.duration_millis / 1000 AS media_size,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.impressions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM video
  WHERE
    campaign.advertising_channel_type =  DEMAND_GEN
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0

  def __post_init__(self) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)


@dataclasses.dataclass
class AppAssetPerformance(PerformanceQuery):
  """Fetches asset performance for App campaigns."""

  query_text = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    asset.id AS asset_id,
    {media_name} AS media_name,
    {media_url} AS media_url,
    {aspect_ratio} AS aspect_ratio,
    {size} AS media_size,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.biddable_app_install_conversions AS installs,
    metrics.biddable_app_post_install_conversions AS inapps,
    metrics.conversions_value AS conversions_value
  FROM ad_group_ad_asset_view
  WHERE
    campaign.advertising_channel_type = MULTI_CHANNEL
    AND asset.type = {media_type}
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0

  def __post_init__(self) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    if self.media_type == 'IMAGE':
      self.media_url = 'asset.image_asset.full_size.url'
      self.aspect_ratio = (
        'asset.image_asset.full_size.width_pixels / '
        'asset.image_asset.full_size.height_pixels'
      )
      self.size = 'asset.image_asset.file_size / 1024'
      self.media_name = 'asset.name'
    else:
      self.media_url = 'asset.youtube_video_asset.youtube_video_id'
      self.aspect_ratio = 0.0
      self.size = 0.0
      self.media_name = 'asset.youtube_video_asset.youtube_video_title'


YOUTUBE_VIDEO_ORIENTATIONS_QUERY: Final[str] = """
SELECT
  id,
  player.embedWidth AS width,
  player.embedHeight AS height
FROM videos
"""

QUERIES_MAPPING: dict[
  str, base_query.BaseQuery | dict[str, base_query.BaseQuery]
] = {
  'app': AppAssetPerformance,
  'display': DisplayAssetPerformance,
  'pmax': PmaxAssetInfo,
  'video': VideoPerformance,
  'demandgen': {
    'YOUTUBE_VIDEO': DemandGenVideoAssetPerformance,
    'IMAGE': DemandGenImageAssetPerformance,
  },
}

CAMPAIGN_TYPES_MAPPING: dict[str, str] = {
  'app': 'MULTI_CHANNEL',
  'display': 'DISPLAY',
  'pmax': 'PERFORMANCE_MAX',
  'video': 'VIDEO',
  'demandgen': 'DEMAND_GEN',
}
