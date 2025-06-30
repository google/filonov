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


@pytest.mark.similarity
class TestMediaSimilarity:
  def test_cluster(self):
    filonov_media_identifier_1 = os.getenv('FILONOV_MEDIA_IDENTIFIER_1')
    filonov_media_identifier_2 = os.getenv('FILONOV_MEDIA_IDENTIFIER_2')
    filonov_media_identifier_3 = os.getenv('FILONOV_MEDIA_IDENTIFIER_3')
    db_uri = os.getenv('FILONOV_DB_URI')

    command = (
      'media-similarity cluster '
      f'{filonov_media_identifier_1} '
      f'{filonov_media_identifier_2} '
      f'{filonov_media_identifier_3} '
      '--media-type YOUTUBE_VIDEO '
      f'--tagger gemini --db-uri {db_uri} --writer console'
    )
    result = subprocess.run(command, shell=True, check=False)
    assert result.returncode == 0

  def test_search(self):
    filonov_media_identifier_1 = os.getenv('FILONOV_MEDIA_IDENTIFIER_1')
    filonov_media_identifier_2 = os.getenv('FILONOV_MEDIA_IDENTIFIER_2')
    db_uri = os.getenv('FILONOV_DB_URI')
    command = (
      'media-similarity search '
      f'{filonov_media_identifier_1} '
      f'{filonov_media_identifier_2} '
      '--media-type YOUTUBE_VIDEO '
      f'--db-uri {db_uri}  --writer console'
    )
    result = subprocess.run(command, shell=True, check=False)
    assert result.returncode == 0

  def test_compare(self):
    filonov_media_identifier_1 = os.getenv('FILONOV_MEDIA_IDENTIFIER_1')
    filonov_media_identifier_2 = os.getenv('FILONOV_MEDIA_IDENTIFIER_2')
    db_uri = os.getenv('FILONOV_DB_URI')
    command = (
      'media-similarity compare '
      f'{filonov_media_identifier_1} '
      f'{filonov_media_identifier_2} '
      '--media-type YOUTUBE_VIDEO '
      f'--db-uri {db_uri}  --writer console'
    )
    result = subprocess.run(command, shell=True, check=False)
    assert result.returncode == 0
