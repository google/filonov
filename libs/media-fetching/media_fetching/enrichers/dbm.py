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

"""Bid Manager specific enrichers."""

import functools

import garf_bid_manager
from garf_core import report

from media_fetching import exceptions
from media_fetching.enrichers import extra_info


class BidManagerEnricherError(exceptions.MediaFetchingError):
  """BidManager specific exceptions for enricher."""


class BidManagerEnricher:
  """Injects BidManager specific information into existing reports."""

  def __init__(self, **kwargs: str) -> None:
    """Initializes MediaTaggingEnricher."""
    self.kwargs = kwargs

  @functools.cached_property
  def fetcher(self) -> garf_bid_manager.BidManagerApiReportFetcher:
    return garf_bid_manager.BidManagerApiReportFetcher(**self.kwargs)

  def brand_lift(
    self,
    performance: report.GarfReport,
    advertiser: str,
    start_date: str,
    end_date: str,
    campaigns: str = '',
    **kwargs: str,
  ) -> extra_info.ExtraInfo:
    """Adds Brand lift metrics to each media_url.

    Args:
      performance: Report with performance data.

    Returns:
      Mapping between media_url and brand lift metrics.
    """
    if 'ad_group_id' not in performance.column_names:
      raise BidManagerEnricherError(
        '"ad_group_id" is required for "brand_lift" enriching'
      )
    query = """
        SELECT
          trueview_ad_group_id AS ad_group_id,
          advertiser_currency AS currency,
          brand_lift_type AS brand_lift_type,
          metric_brand_lift_absolute_brand_lift
            AS brand_lift_absolute_brand_lift,
          metric_brand_lift_all_survey_responses
            AS brand_lift_all_survey_responses,
          metric_brand_lift_baseline_positive_response_rate
           AS brand_lift_baseline_positive_response_rate,
          metric_brand_lift_baseline_survey_responses
            AS brand_lift_baseline_survey_responses,
          metric_brand_lift_cost_per_lifted_user
            AS brand_lift_cost_per_lifted_user,
          metric_brand_lift_exposed_survey_responses
            AS brand_lift_exposed_survey_responses,
          metric_brand_lift_headroom_brand_lift
            AS brand_lift_headroom_brand_lift,
          metric_brand_lift_relative_brand_lift
            AS brand_lift_relative_brand_lift,
          metric_brand_lift_users AS brand_lift_users,
        FROM youtube
        WHERE advertiser IN ({advertiser})
        AND dataRange IN ({start_date}, {end_date})
        {campaigns}
      """
    brand_lift_data = self.fetcher.fetch(
      query.format(
        advertiser=advertiser,
        campaigns=campaigns,
        start_date=start_date,
        end_date=end_date,
      )
    )
    return extra_info.ExtraInfo(
      info={
        ad_group_id: values[0]
        for ad_group_id, values in brand_lift_data.to_dict(
          key_column='ad_group_id'
        ).items()
      },
      base_key='ad_group_id',
    )
