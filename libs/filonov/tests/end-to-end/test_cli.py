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

db_uri = os.getenv('FILONOV_DB_URI')
filonov_performance_file = os.getenv('FILONOV_PERFORMANCE_RESULTS')
filonov_account = os.getenv('FILONOV_GOOGLEADS_ACCOUNT')
filonov_youtube_channel = os.getenv('FILONOV_YOUTUBE_CHANNEL_ID')


@pytest.mark.filonov
class TestFilonov:
  def test_source_file(self):
    command = (
      'filonov --source file --media-type IMAGE '
      '--tagger=gemini '
      f'--db-uri  {db_uri} '
      f'--file.path={filonov_performance_file} '
      '--file.media_identifier=media_url '
      '--file.media_name=asset_name '
      '--file.metrics=clicks '
      '--logger local'
    )
    result = subprocess.run(command, shell=True, check=False)
    assert result.returncode == 0

  def test_source_googleads(self):
    command = (
      'filonov --source googleads --media-type IMAGE '
      '--tagger=gemini '
      f'--db-uri  {db_uri} '
      f'--googleads.account={filonov_account} '
      '--googleads.campaign_types=pmax '
      '--logger local'
    )
    result = subprocess.run(command, shell=True, check=False)
    assert result.returncode == 0

  def test_source_youtube(self):
    command = (
      'filonov --source youtube '
      f'--db-uri  {db_uri} '
      f'--youtube.channel={filonov_youtube_channel} '
      '--logger local'
    )
    result = subprocess.run(command, shell=True, check=False)
    assert result.returncode == 0
