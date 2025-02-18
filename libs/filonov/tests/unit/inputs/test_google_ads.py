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
import gaarf
import pytest
from filonov.inputs import google_ads


class TestExtraInfoFetcher:
  @pytest.fixture
  def info_fetcher(self):
    return google_ads.ExtraInfoFetcher(None, None)

  def test_inject_extra_info(self, info_fetcher):
    performance_report = gaarf.GaarfReport(
      results=[['media_1', 1], ['media_2', 10]],
      column_names=['media_url', 'clicks'],
    )
    extra_info = {'media_1': {'size': 2, 'aspect_ratio': 3}}

    info_fetcher._inject_extra_info_into_reports(
      performance_report, extra_info, columns=('size', 'aspect_ratio')
    )

    expected_report = gaarf.GaarfReport(
      results=[
        ['media_1', 1, 2, 3],
        ['media_2', 10, None, None],
      ],
      column_names=['media_url', 'clicks', 'size', 'aspect_ratio'],
    )

    assert performance_report == expected_report
