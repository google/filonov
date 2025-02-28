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

import garf_core
import pytest
from filonov.inputs import file, interfaces
from garf_io.writers import csv_writer


class TestExtraInfoFetcher:
  @pytest.fixture
  def tmp_folder(self, tmp_path):
    return tmp_path

  @pytest.fixture
  def fetcher(self):
    return file.ExtraInfoFetcher()

  def test_generate_extra_info_returns_correct_result(
    self, fetcher, tmp_folder
  ):
    youtube_video_id = 'a1234567890'
    youtube_link = f'https://www.youtube.com/watch?v={youtube_video_id}'
    fake_report = garf_core.report.GarfReport(
      results=[
        [youtube_video_id, 'test_video', '10', 100, 10],
      ],
      column_names=[
        'media_url',
        'media_name',
        'video_duration',
        'views',
        'likes',
      ],
    )
    csv_writer.CsvWriter(tmp_folder).write(fake_report, 'test')

    media_info = fetcher.generate_extra_info(
      file.FileInputParameters(
        path=tmp_folder / 'test.csv',
        media_identifier='media_url',
        media_name='media_name',
        metric_names=('views', 'likes'),
      ),
      media_type='YOUTUBE_VIDEO',
    )
    expected_media_info = {
      youtube_video_id: interfaces.MediaInfo(
        media_path=youtube_link,
        media_name='test_video',
        series={},
        media_preview=f'https://img.youtube.com/vi/{youtube_video_id}/0.jpg',
        info={
          'views': 100,
          'likes': 10,
          'video_duration': 10,
          'orientation': None,
        },
        segments={},
        size=None,
      )
    }
    assert media_info == expected_media_info
