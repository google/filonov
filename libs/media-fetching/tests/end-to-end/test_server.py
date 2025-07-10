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
import media_fetching
import pytest
from fastapi import testclient
from media_fetching.entrypoints.server import router

app = fastapi.FastAPI()
app.include_router(router)
client = testclient.TestClient(app)

dotenv.load_dotenv()
_SCRIPT_PATH = pathlib.Path(__file__).parent

filonov_performance_file = os.getenv('FILONOV_PERFORMANCE_RESULTS')
filonov_account = os.getenv('FILONOV_GOOGLEADS_ACCOUNT')
filonov_youtube_channel = os.getenv('FILONOV_YOUTUBE_CHANNEL_ID')


@pytest.mark.tagger
class TestMediaFetcher:
  @pytest.mark.googleads
  class TestGoogleAdsFetcher:
    @pytest.mark.parametrize(
      'media_type',
      ['IMAGE', 'YOUTUBE_VIDEO'],
    )
    def test_fetch(self, media_type):
      request = {
        'request': {
          'media_type': media_type,
          'account': filonov_account,
          'campaign_types': ['pmax'],
        },
        'writer_options': {
          'writer': 'console',
        },
      }
      response = client.post('/media_fetching/fetch:googleads', json=request)
      assert response.status_code == fastapi.status.HTTP_200_OK

  @pytest.mark.youtube
  class TestYouTubeFetcher:
    def test_fetch(self):
      request = {
        'request': {
          'channel': filonov_youtube_channel,
        },
        'writer_options': {
          'writer': 'console',
        },
      }
      response = client.post('/media_fetching/fetch:youtube', json=request)
      assert response.status_code == fastapi.status.HTTP_200_OK

  @pytest.mark.file
  class TestFileFetcher:
    def test_fetch(self):
      request = {
        'request': {
          'path': str(filonov_performance_file),
        },
        'writer_options': {
          'writer': 'console',
        },
      }
      response = client.post('/media_fetching/fetch:file', json=request)
      assert response.status_code == fastapi.status.HTTP_200_OK
