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
import os
from collections.abc import Sequence
from typing import Literal

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
    asset.id AS asset_id,
    asset.name AS asset_name,
    {media_url} AS media_url,
    metrics.cost_micros / 1e6 AS cost
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
    asset_performance = fetcher.fetch(
      AppAssetPerformance(**dataclasses.asdict(fetching_request)),
      customer_ids,
    )
    return {
      media.convert_path_to_media_name(row.media_url): interfaces.MediaInfo(
        media_path=row.media_url, media_name=row.asset_id, cost=row.cost
      )
      for row in asset_performance
      if row.media_url
    }
