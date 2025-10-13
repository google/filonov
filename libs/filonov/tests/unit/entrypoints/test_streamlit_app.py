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

import filonov
from filonov.entrypoints import streamlit_app


def test_build_cli_command():
  request = filonov.CreativeMapGenerateRequest(
    source='fake',
    media_type='IMAGE',
    tagger='gemini',
  )

  command = streamlit_app.build_cli_command(
    request=request, db='sqlite:///test.db'
  )
  expected_command = (
    'filonov --source fake --media-type IMAGE --tagger gemini '
    '--fake.media_identifier=media_url --fake.media_name=media_name '
    '--fake.metrics=clicks,impressions '
    '--output-name creative_map '
    '--db-uri sqlite:///test.db'
  )
  assert command.replace('\\\n\t', '') == expected_command
