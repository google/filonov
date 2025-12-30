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

"""Google Ads specific enrichers."""

import functools
import os
import pathlib

import garf_google_ads
from garf_core import report

from media_fetching import exceptions
from media_fetching.enrichers import extra_info


class GoogleAdsEnricherError(exceptions.MediaFetchingError):
  """Google Ads specific exceptions for enricher."""


class GoogleAdsEnricher:
  """Injects Google Ads specific information into existing reports."""

  def __init__(
    self,
    account: str,
    ads_config: str | None = None,
    enable_cache: bool = False,
    **kwargs: str,
  ) -> None:
    """Initializes MediaTaggingEnricher."""
    self.account = account
    self.enable_cache = enable_cache
    self.ads_config = ads_config or os.getenv(
      'GOOGLE_ADS_CONFIGURATION_FILE_PATH',
      str(pathlib.Path.home() / 'google-ads.yaml'),
    )
    self.kwargs = kwargs

  @functools.cached_property
  def fetcher(self) -> garf_google_ads.GoogleAdsApiReportFetcher:
    if not self._fetcher:
      self._fetcher = garf_google_ads.GoogleAdsApiReportFetcher(
        api_client=garf_google_ads.api_clients.GoogleAdsApiClient(
          path_to_config=self.ads_config
        ),
        enable_cache=self.enable_cache,
      )
    return self._fetcher

  @functools.cached_property
  def accounts(self) -> list[str]:
    return self.fetcher.expand_mcc(self.account)

  def approval_rate(
    self, performance: report.GarfReport, **kwargs: str
  ) -> extra_info.ExtraInfo:
    """Calculates percentage of approvals for each media.

    Args:
      performance: Report with performance data.

    Returns:
      Mapping between media_url and approval rate (from 0 to 1).
    """
    approvals = performance.to_dict(
      key_column='media_url', value_column='approval_status'
    )
    approval_rates = {}
    for media_url, statuses in approvals.items():
      approval_rate = 1 - len(
        list(filter(lambda x: x != 'APPROVED', statuses))
      ) / len(statuses)

      approval_rates[media_url] = {'approval_rate': approval_rate}
    return extra_info.ExtraInfo(info=approval_rates)

  def main_geo(
    self, performance: report.GarfReport, **kwargs: str
  ) -> extra_info.ExtraInfo:
    """Calculates dominant country for each media.

    Dominant country is calculated on campaign level based on >50% of all
    spend and propagated to all media in this campaign.

    Args:
      performance: Report with performance data.

    Returns:
      Mapping between media_url and its dominant country.

    Raises:
      GoogleAdsEnricherError: If report does not have campaign_id column.
    """
    if 'campaign_id' not in performance.column_names:
      raise GoogleAdsEnricherError(
        '"campaign_id" is required for "main_geo" enriching'
      )
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
    return extra_info.ExtraInfo(
      info={
        campaign_id: {'main_geo': value}
        for campaign_id, value in geo_info.items()
      },
      base_key='campaign_id',
    )
