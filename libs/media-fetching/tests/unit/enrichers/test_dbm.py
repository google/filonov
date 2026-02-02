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
from garf.core import report
from media_fetching.enrichers import dbm, extra_info


class TestBidManagerEnricher:
  @pytest.fixture
  def enricher(self):
    return dbm.BidManagerEnricher()

  def test_brand_lift_enricher(self, mocker, enricher):
    performance_report = report.GarfReport(
      results=[[1]], column_names=['ad_group_id']
    )
    fake_report = report.GarfReport(
      results=[
        [1, 'CONSIDERATION', 100],
        [2, 'AWARENESS', 1000],
      ],
      column_names=[
        'ad_group_id',
        'brand_lift_type',
        'brand_lift_absolute_brand_lift',
      ],
    )
    mocker.patch(
      'garf.community.google.bid_manager.report_fetcher.BidManagerApiReportFetcher.fetch',
      return_value=fake_report,
    )

    test_info = enricher.brand_lift(
      performance=performance_report,
      advertiser='',
      start_date='',
      end_date='',
      campaigns='',
    )
    expected_info = extra_info.ExtraInfo(
      info={
        1: {
          'brand_lift_type': 'CONSIDERATION',
          'brand_lift_absolute_brand_lift': 100,
        },
        2: {
          'brand_lift_type': 'AWARENESS',
          'brand_lift_absolute_brand_lift': 1000,
        },
      },
      base_key='ad_group_id',
    )
    assert test_info == expected_info
