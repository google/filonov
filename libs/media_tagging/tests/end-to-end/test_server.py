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
import media_tagging
from fastapi import testclient
from media_tagging.entrypoints.server import router

app = fastapi.FastAPI()
app.include_router(router)
client = testclient.TestClient(app)

dotenv.load_dotenv()
_SCRIPT_PATH = pathlib.Path(__file__).parent
_IMAGE_PATH = str(_SCRIPT_PATH / os.getenv('FILONOV_IMAGE_PATH'))


class TestGeminiTagger:
  tagger = 'gemini'

  def test_tag(self):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type='IMAGE',
      media_paths=[_IMAGE_PATH],
    )
    response = client.post('/media_tagging/tag', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_200_OK

    result = media_tagging.tagging_result.TaggingResult(
      **response.json().get('results')[0]
    )

    assert result.identifier == 'test_image'
    assert result.output == 'tag'
    assert result.type == 'image'
    assert result.tagger == self.tagger
    assert isinstance(result.content[0], media_tagging.tagging_result.Tag)

  def test_describe(self):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type='IMAGE',
      media_paths=[_IMAGE_PATH],
    )
    response = client.post('/media_tagging/describe', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_200_OK

    result = media_tagging.tagging_result.TaggingResult(
      **response.json().get('results')[0]
    )

    assert result.identifier == 'test_image'
    assert result.output == 'description'
    assert result.type == 'image'
    assert result.tagger == self.tagger
    assert isinstance(result.content, media_tagging.tagging_result.Description)


class TestGoogleCloudTagger:
  tagger = 'google-cloud'

  def test_tag(self):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type='IMAGE',
      media_paths=[_IMAGE_PATH],
    )
    response = client.post('/media_tagging/tag', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_200_OK

    result = media_tagging.tagging_result.TaggingResult(
      **response.json().get('results')[0]
    )

    assert result.identifier == 'test_image'
    assert result.output == 'tag'
    assert result.type == 'image'
    assert result.tagger == self.tagger
    assert isinstance(result.content[0], media_tagging.tagging_result.Tag)

  def test_describe(self):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type='IMAGE',
      media_paths=[_IMAGE_PATH],
    )
    response = client.post('/media_tagging/describe', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_404_NOT_FOUND
    assert response.json().get('detail') == 'describe method is not supported'
