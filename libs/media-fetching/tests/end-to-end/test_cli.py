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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring, missing-function-docstring

import os
import pathlib
import subprocess

import dotenv
import pytest

dotenv.load_dotenv()
_SCRIPT_PATH = pathlib.Path(__file__).parent

filonov_performance_file = os.getenv('FILONOV_PERFORMANCE_RESULTS')
filonov_account = os.getenv('FILONOV_GOOGLEADS_ACCOUNT')
filonov_youtube_channel = os.getenv('FILONOV_YOUTUBE_CHANNEL_ID')
filonov_db = os.getenv('FILONOV_TEST_DB')
filonov_bq_table = os.getenv('FILONOV_TEST_BQ_TABLE')


@pytest.mark.tagger
class TestMediaFetcher:
  @pytest.mark.googleads
  class TestGoogleAdsFetcher:
    @pytest.mark.parametrize(
      'media_type',
      ['IMAGE', 'YOUTUBE_VIDEO'],
    )
    def test_fetch(self, media_type):
      command = (
        'media-fetcher --source googleads '
        f'--media-type {media_type} '
        f'--googleads.account={filonov_account} '
        '--googleads.campaign-types=pmax '
        '--extra-info=googleads.main_geo '
        '--writer console '
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0

  @pytest.mark.youtube
  class TestYouTubeFetcher:
    def test_fetch(self):
      command = (
        'media-fetcher --source youtube '
        f'--youtube.channel={filonov_youtube_channel} '
        '--writer console '
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0

  @pytest.mark.file
  class TestFileFetcher:
    def test_fetch(self):
      command = (
        'media-fetcher --source file '
        f'--file.path={filonov_performance_file} '
        '--file.media-identifier=media_url '
        '--file.media-name=asset_name '
        '--file.metrics=clicks '
        '--writer console '
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0

  @pytest.mark.sqldb
  class TestSqlAlchemyQueryFetcher:
    def test_fetch(self):
      command = (
        'media-fetcher --source sqldb '
        f'--sqldb.connection-string={filonov_db} '
        '--sqldb.table=media_results '
        '--writer console '
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0

  @pytest.mark.bq
  class TestBigQueryFetcher:
    def test_fetch(self):
      command = (
        'media-fetcher --source bq '
        f'--bq.table={filonov_bq_table} '
        '--writer console '
      )
      result = subprocess.run(command, shell=True, check=False)
      assert result.returncode == 0
