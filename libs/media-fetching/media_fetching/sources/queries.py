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

"""Contains Google Ads API queries."""

from __future__ import annotations

import warnings
from typing import ClassVar, Literal

import pydantic
from garf_core import base_query

warnings.filterwarnings('ignore', category=UserWarning)
SupportedMediaTypes = Literal['IMAGE', 'YOUTUBE_VIDEO', 'TEXT']
SupportedCampaignTypes = Literal[
  'pmax', 'app', 'demandgen', 'video', 'display', 'search'
]


class PerformanceQuery(base_query.BaseQuery, pydantic.BaseModel):
  """Enforces presence of certain fields in the query.

  Attributes:
    base_query_text:
      A Gaarf query text template that contains aliases specified
      in `required_fields`.

  Raises:
    ValueError:
      If subclass query_text does not contain all required fields.
  """

  model_config = pydantic.ConfigDict(extra='allow')
  query_text: str = ''
  required_fields: ClassVar[tuple[str, ...]] = (
    'date',
    'campaign_type',
    'channel_type',
    'format_type',
    'media_name',
    'media_url',
    'aspect_ratio',
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
        f'query_text does not contain required fields: {missing_fields}'
      )


class DisplayAssetPerformance(PerformanceQuery):
  """Fetches image ads performance for Display campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    campaign.advertising_channel_type AS channel_type,
    ad_group_ad.ad.name AS media_name,
    ad_group_ad.ad.id AS asset_id,
    ad_group_ad.ad.image_ad.image_url AS media_url,
    'UNKNOWN' AS format_type,
    ad_group_ad.ad.image_ad.pixel_width / ad_group_ad.ad.image_ad.pixel_height
      AS aspect_ratio,
    0 AS file_size,
    ad_group_ad.policy_summary.approval_status AS approval_status,
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
    AND ad_group_ad.ad.image_ad.image_url != ''
    AND metrics.cost_micros > {min_cost}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.query_text = self.query_text.format(**self.model_dump())


class VideoPerformance(PerformanceQuery):
  """Fetches video ad performance for Video campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    campaign.id AS campaign_id,
    segments.date AS date,
    campaign.advertising_channel_type AS channel_type,
    ad_group_ad.ad.type AS ad_type,
    video.id AS media_url,
    video.title AS media_name,
    segments.ad_format_type AS format_type,
    0 AS aspect_ratio,
    video.duration_millis / 1000 AS video_duration,
    ad_group_ad.policy_summary.approval_status AS approval_status,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM video
  WHERE
    campaign.advertising_channel_type = VIDEO
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND video.id != ''
    AND metrics.cost_micros > {min_cost}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.query_text = self.query_text.format(**self.model_dump())


class PmaxAssetPerformance(PerformanceQuery):
  """Fetches asset info for Performance Max campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    campaign.advertising_channel_type AS channel_type,
    asset.id AS asset_id,
    {media_name} AS media_name,
    {media_url} AS media_url,
    asset_group_asset.field_type AS format_type,
    {aspect_ratio} AS aspect_ratio,
    {size} AS {size_column},
    asset_group_asset.policy_summary.approval_status AS approval_status,
    0 AS cost,
    0 AS clicks,
    0 AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM asset_group_asset
  WHERE
    asset.type = {media_type}
    AND campaign.advertising_channel_type = PERFORMANCE_MAX
    AND {media_url} != ''
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    if self.media_type == 'IMAGE':
      self.media_url = 'asset.image_asset.full_size.url'
      self.aspect_ratio = (
        'asset.image_asset.full_size.width_pixels / '
        'asset.image_asset.full_size.height_pixels'
      )
      self.size = 'asset.image_asset.file_size / 1024'
      self.size_column = 'file_size'
      self.media_name = 'asset.name'
    elif self.media_type == 'TEXT':
      self.media_url = 'asset.text_asset.text'
      self.aspect_ratio = '0'
      self.size = '0'
      self.size_column = 'file_size'
      self.media_name = 'asset.text_asset.text'
    else:
      self.media_url = 'asset.youtube_video_asset.youtube_video_id'
      self.aspect_ratio = 0.0
      self.size = 0.0
      self.size_column = 'video_duration'
      self.media_name = 'asset.youtube_video_asset.youtube_video_title'
    self.query_text = self.query_text.format(**self.model_dump())


class SearchAssetPerformance(PerformanceQuery):
  """Fetches text asset performance for Search campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    campaign.advertising_channel_type AS channel_type,
    asset.text_asset.text AS media_name,
    asset.id AS asset_id,
    asset.text_asset.text AS media_url,
    ad_group_ad_asset_view.field_type AS format_type,
    0 AS aspect_ratio,
    0 AS file_size,
    ad_group_ad.ad.name AS ad_name,
    ad_group_ad_asset_view.policy_summary:approval_status AS approval_status,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM ad_group_ad_asset_view
  WHERE
    campaign.advertising_channel_type =  SEARCH
    AND asset.type = TEXT
    AND asset.text_asset.text != ''
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.query_text = self.query_text.format(**self.model_dump())


class DemandGenTextAssetPerformance(PerformanceQuery):
  """Fetches image asset performance for Demand Gen campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    campaign.advertising_channel_type AS channel_type,
    asset.text_asset.text AS media_name,
    asset.id AS asset_id,
    asset.text_asset.text AS media_url,
    ad_group_ad_asset_view.field_type AS format_type,
    0 AS aspect_ratio,
    0 AS file_size,
    ad_group_ad.ad.name AS ad_name,
    ad_group_ad_asset_view.policy_summary:approval_status AS approval_status,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM ad_group_ad_asset_view
  WHERE
    campaign.advertising_channel_type =  DEMAND_GEN
    AND asset.type = TEXT
    AND asset.text_asset.text != ''
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND metrics.cost_micros > {min_cost}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.query_text = self.query_text.format(**self.model_dump())


class DemandGenImageAssetPerformance(PerformanceQuery):
  """Fetches image asset performance for Demand Gen campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    campaign.advertising_channel_type AS channel_type,
    asset.name AS media_name,
    asset.id AS asset_id,
    asset.image_asset.full_size.url AS media_url,
    ad_group_ad_asset_view.field_type AS format_type,
    asset.image_asset.full_size.width_pixels /
      asset.image_asset.full_size.height_pixels AS aspect_ratio,
    asset.image_asset.file_size / 1024 AS file_size,
    ad_group_ad.ad.name AS ad_name,
    ad_group_ad_asset_view.policy_summary:approval_status AS approval_status,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM ad_group_ad_asset_view
  WHERE
    campaign.advertising_channel_type =  DEMAND_GEN
    AND asset.type = IMAGE
    AND ad_group_ad_asset_view.field_type NOT IN (
      BUSINESS_LOGO, LANDSCAPE_LOGO,  LOGO
    )
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND asset.image_asset.full_size.url != ''
    AND metrics.cost_micros > {min_cost}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.query_text = self.query_text.format(**self.model_dump())


class DemandGenVideoAssetPerformance(PerformanceQuery):
  """Fetches video asset performance for Demand Gen campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    campaign.advertising_channel_type AS channel_type,
    video.id AS media_url,
    video.title AS media_name,
    segments.ad_format_type AS format_type,
    0 AS aspect_ratio,
    video.duration_millis / 1000 AS video_duration,
    ad_group_ad.policy_summary.approval_status AS approval_status,
    metrics.cost_micros / 1e6 AS cost,
    metrics.clicks AS clicks,
    metrics.impressions AS impressions,
    metrics.conversions AS conversions,
    metrics.conversions_value AS conversions_value
  FROM video
  WHERE
    campaign.advertising_channel_type =  DEMAND_GEN
    AND segments.date BETWEEN '{start_date}' AND '{end_date}'
    AND video.id != ''
    AND metrics.cost_micros > {min_cost}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.min_cost = int(self.min_cost * 1e6)
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.query_text = self.query_text.format(**self.model_dump())


class AppAssetPerformance(PerformanceQuery):
  """Fetches asset performance for App campaigns."""

  query_text: str = """
  SELECT
    '{campaign_type}' AS campaign_type,
    segments.date AS date,
    campaign.id AS campaign_id,
    asset.id AS asset_id,
    {media_name} AS media_name,
    {media_url} AS media_url,
    ad_group_ad_asset_view.field_type AS format_type,
    {aspect_ratio} AS aspect_ratio,
    {size} AS {size_column},
    ad_group_ad_asset_view.policy_summary:approval_status AS approval_status,
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
    AND {media_url} != ''
    AND metrics.cost_micros > {min_cost}
    {app_id}
    {campaign_ids}
  """

  start_date: str
  end_date: str
  media_type: SupportedMediaTypes
  campaign_type: SupportedCampaignTypes
  min_cost: int = 0
  app_id: str | None = None
  campaign_ids: list[int] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    self.app_id = (
      f'AND campaign.app_campaign_setting.app_id = "{self.app_id}"'
      if self.app_id
      else ''
    )
    self.campaign_ids = _format_campaign_ids(self.campaign_ids)
    self.min_cost = int(self.min_cost * 1e6)
    if self.media_type == 'IMAGE':
      self.media_url = 'asset.image_asset.full_size.url'
      self.aspect_ratio = (
        'asset.image_asset.full_size.width_pixels / '
        'asset.image_asset.full_size.height_pixels'
      )
      self.size = 'asset.image_asset.file_size / 1024'
      self.size_column = 'file_size'
      self.media_name = 'asset.name'
    elif self.media_type == 'TEXT':
      self.media_url = 'asset.text_asset.text'
      self.aspect_ratio = '0'
      self.size = '0'
      self.size_column = 'file_size'
      self.media_name = 'asset.text_asset.text'
    else:
      self.media_url = 'asset.youtube_video_asset.youtube_video_id'
      self.aspect_ratio = 0.0
      self.size = 0.0
      self.size_column = 'video_duration'
      self.media_name = 'asset.youtube_video_asset.youtube_video_title'
    self.query_text = self.query_text.format(**self.model_dump())


QUERIES_MAPPING: dict[
  str, base_query.BaseQuery | dict[str, base_query.BaseQuery]
] = {
  'search': SearchAssetPerformance,
  'app': AppAssetPerformance,
  'display': DisplayAssetPerformance,
  'pmax': PmaxAssetPerformance,
  'video': VideoPerformance,
  'demandgen': {
    'YOUTUBE_VIDEO': DemandGenVideoAssetPerformance,
    'IMAGE': DemandGenImageAssetPerformance,
    'TEXT': DemandGenTextAssetPerformance,
  },
}

CAMPAIGN_TYPES_MAPPING: dict[str, str] = {
  'app': 'MULTI_CHANNEL',
  'search': 'SEARCH',
  'display': 'DISPLAY',
  'pmax': 'PERFORMANCE_MAX',
  'video': 'VIDEO',
  'demandgen': 'DEMAND_GEN',
}


def _format_campaign_ids(campaign_ids: list[str] | None) -> str:
  if campaign_ids:
    campaign_ids_joined = ','.join(
      str(campaign_id) for campaign_id in campaign_ids
    )
    return f'AND campaign.id IN ({campaign_ids_joined})'
  return ''
