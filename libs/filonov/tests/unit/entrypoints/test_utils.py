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

import filonov
import pytest
from filonov.entrypoints import utils


@pytest.mark.parametrize(
  'path, expected',
  [
    ('creative_map', './creative_map.json'),
    ('creative_map.json', './creative_map.json'),
    ('/app/creative_map', './app/creative_map.json'),
    # ('../app/creative_map', './app/creative_map.json'),
    ('/app/creative_map.json', './app/creative_map.json'),
  ],
)
def test_build_creative_map_destination_returns_correct_file_name(
  path: str, expected: str
):
  result = utils.build_creative_map_destination(path)
  assert result == expected


@pytest.mark.parametrize(
  'path, expected',
  [
    ('gs://bucket/creative_map', 'gs://bucket/creative_map.json'),
    ('gs://bucket/creative_map.json', 'gs://bucket/creative_map.json'),
    ('/app/creative_map', 'gs://bucket/app/creative_map.json'),
  ],
)
def test_build_creative_map_destination_returns_correct_remote_file_name(
  monkeypatch, path: str, expected: str
):
  monkeypatch.setenv('FILONOV_OUTPUT_DIR', 'gs://bucket/')
  result = utils.build_creative_map_destination(path)
  assert result == expected


@pytest.mark.parametrize(
  'path, error',
  [
    ('gs://wrong-bucket/creative_map', 'Remote file location mismatch'),
    (
      '../other-bucket/creative_map',
      'Overwriting filonov directory not allowed',
    ),
  ],
)
def test_build_creative_map_destination_raises_error_from_remote_file_mismatch(
  monkeypatch, path: str, error: str
):
  monkeypatch.setenv('FILONOV_OUTPUT_DIR', 'gs://bucket/')
  with pytest.raises(filonov.exceptions.FilonovError, match=error):
    utils.build_creative_map_destination(path)


def test_build_cli_command_map():
  request = filonov.GenerateCreativeMapRequest(
    source='fake',
    media_type='IMAGE',
    tagger='gemini',
  )

  command = utils.build_cli_command(
    request=request, output='map', db='sqlite:///test.db'
  )
  expected_command = (
    'filonov --source fake --media-type IMAGE --tagger gemini '
    '--fake.media_identifier=media_url --fake.media_name=media_name '
    '--fake.metrics=clicks,impressions '
    '--output map '
    '--db-uri sqlite:///test.db'
  )
  assert command.replace('\\\n\t', '') == expected_command


def test_build_cli_command_tables():
  request = filonov.GenerateTablesRequest(
    source='fake', media_type='IMAGE', tagger='gemini', writer='csv'
  )

  command = utils.build_cli_command(
    request=request, output='tables', db='sqlite:///test.db'
  )
  expected_command = (
    'filonov --source fake --media-type IMAGE --tagger gemini '
    '--fake.media_identifier=media_url --fake.media_name=media_name '
    '--fake.metrics=clicks,impressions '
    '--output tables '
    '--writer csv '
    '--db-uri sqlite:///test.db'
  )
  assert command.replace('\\\n\t', '') == expected_command
