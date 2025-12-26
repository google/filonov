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
    ('creative_map', 'creative_map.json'),
    ('creative_map.json', 'creative_map.json'),
    ('/app/creative_map', '/app/creative_map.json'),
    ('/app/creative_map.json', '/app/creative_map.json'),
    ('gs://bucket/creative_map', 'gs://bucket/creative_map.json'),
    ('gs://bucket/creative_map.json', 'gs://bucket/creative_map.json'),
  ],
)
def test_build_creative_map_destination_returns_correct_file_name(
  path: str, expected: str
):
  result = utils.build_creative_map_destination(path)
  assert result == expected


def test_build_cli_command():
  request = filonov.GenerateCreativeMapRequest(
    source='fake',
    media_type='IMAGE',
    tagger='gemini',
  )

  command = utils.build_cli_command(request=request, db='sqlite:///test.db')
  expected_command = (
    'filonov --source fake --media-type IMAGE --tagger gemini '
    '--fake.media_identifier=media_url --fake.media_name=media_name '
    '--fake.metrics=clicks,impressions '
    '--output-name creative_map '
    '--db-uri sqlite:///test.db'
  )
  assert command.replace('\\\n\t', '') == expected_command
