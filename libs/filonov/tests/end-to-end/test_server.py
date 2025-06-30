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

import dotenv
import fastapi
import filonov
from fastapi import testclient
from filonov.entrypoints import server

app = fastapi.FastAPI()
app.include_router(server.router)
client = testclient.TestClient(app)

dotenv.load_dotenv()
_SCRIPT_PATH = pathlib.Path(__file__).parent


class TestFilonov:
  def test_source_file(self):
    request = filonov.CreativeMapGenerateRequest(
      source='file',
      media_type='IMAGE',
      tagger='gemini',
      input_parameters={
        'path': str(_SCRIPT_PATH / os.getenv('FILONOV_PERFORMANCE_RESULTS')),
      },
    )
    response = client.post(
      '/creative_maps/generate:file', json=request.model_dump()
    )
    assert response.status_code == fastapi.status.HTTP_200_OK

  def test_source_googleads(self):
    request = filonov.CreativeMapGenerateRequest(
      source='googleads',
      media_type='IMAGE',
      tagger='gemini',
      input_parameters={
        'account': os.getenv('FILONOV_GOOGLEADS_ACCOUNT'),
        'media_type': 'IMAGE',
        'campaign_types': ('pmax',),
      },
    )
    response = client.post(
      '/creative_maps/generate:googleads', json=request.model_dump()
    )
    assert response.status_code == fastapi.status.HTTP_200_OK

  def test_source_youtube(self):
    request = filonov.CreativeMapGenerateRequest(
      source='youtube',
      input_parameters={
        'channel': os.getenv('FILONOV_YOUTUBE_CHANNEL_ID'),
      },
    )
    response = client.post(
      '/creative_maps/generate:youtube', json=request.model_dump()
    )
    assert response.status_code == fastapi.status.HTTP_200_OK
