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

from media_fetching.sources import googleads, queries


class TestGoogleAdsFetchingParameters:
  def test_query_params_returns_extra_arguments(self):
    test_app_id = 'com.example'
    params = googleads.GoogleAdsFetchingParameters(
      account='1234567890', app_id=test_app_id
    )
    assert params.query_params.get('app_id') == test_app_id

    query = queries.AppAssetPerformance(
      **params.query_params, campaign_type='app'
    )

    assert f'AND campaign.app_campaign_setting.app_id = "{test_app_id}"' in str(
      query
    )
