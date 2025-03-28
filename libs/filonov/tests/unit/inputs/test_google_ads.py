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
from filonov.inputs import google_ads, interfaces


class TestExtraInfoFetcher:
  @pytest.fixture
  def fetcher(self):
    return google_ads.ExtraInfoFetcher()

  def test_generate_extra_info_returns_correct_result(self, fetcher, mocker):
    youtube_video_id = '12345678900'
    youtube_link = f'https://www.youtube.com/watch?v={youtube_video_id}'
    fake_report = gaarf.GaarfReport(
      results=[
        [
          '2025-01-01',
          youtube_video_id,
          'test_video',
          'app',
          '10',
          100,
          10,
          10,
          0,
          0,
          'Portrait',
        ],
      ],
      column_names=[
        'date',
        'media_url',
        'media_name',
        'campaign_type',
        'video_duration',
        'clicks',
        'impressions',
        'cost',
        'conversions',
        'conversions_value',
        'orientation',
      ],
    )
    mocker.patch(
      'filonov.inputs.google_ads.ExtraInfoFetcher.fetch_media_data',
      return_value=fake_report,
    )

    media_info = fetcher.generate_extra_info(
      google_ads.GoogleAdsInputParameters(
        account='1234',
      ),
      media_type='YOUTUBE_VIDEO',
    )
    expected_media_info = {
      youtube_video_id: interfaces.MediaInfo(
        media_path=youtube_link,
        media_name='test_video',
        series={
          '2025-01-01': {
            'clicks': 100,
            'impressions': 10,
            'cost': 10,
            'conversions': 0,
            'conversions_value': 0,
          }
        },
        media_preview=f'https://img.youtube.com/vi/{youtube_video_id}/0.jpg',
        info={
          'clicks': 100,
          'impressions': 10,
          'cost': 10,
          'conversions': 0,
          'conversions_value': 0,
          'video_duration': '10',
          'orientation': 'Portrait',
        },
        segments={'campaign_type': 'app'},
        size=None,
      )
    }
    assert media_info == expected_media_info
