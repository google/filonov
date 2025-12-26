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

import pytest
from media_fetching.sources import dbm


class TestBidManagerFetchingParameters:
  @pytest.mark.parametrize(
    ('extra', 'expected'),
    [
      (
        {'metrics': 'clicks,impressions,total_conversions,brand_lift_users'},
        'metric_clicks AS clicks, '
        'metric_impressions AS impressions, '
        'metric_total_conversions AS total_conversions',
      ),
      (
        {'line_item_type': 'Demand Gen, Standard'},
        'AND line_item_type IN (Demand Gen, Standard)',
      ),
    ],
  )
  def test_query_params_returns_extra_arguments(self, extra, expected):
    params = dbm.BidManagerFetchingParameters(advertiser='1234567890', **extra)
    extra_key = list(extra.keys())[0]
    assert params.query_parameters.get(extra_key) == expected
