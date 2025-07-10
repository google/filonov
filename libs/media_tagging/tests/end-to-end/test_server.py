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
import pytest
from fastapi import testclient
from media_tagging import media
from media_tagging.entrypoints.server import router

app = fastapi.FastAPI()
app.include_router(router)
client = testclient.TestClient(app)

dotenv.load_dotenv()
_SCRIPT_PATH = pathlib.Path(__file__).parent
_IMAGE_PATH = str(_SCRIPT_PATH / os.getenv('FILONOV_IMAGE_PATH'))
filonov_test_text = 'To be or not to be this is the question.'


class TestGeminiTagger:
  tagger = 'gemini'

  @pytest.mark.parametrize(
    ('media_type', 'media_location'),
    [
      ('TEXT', filonov_test_text),
      ('IMAGE', _SCRIPT_PATH / os.getenv('FILONOV_IMAGE_PATH')),
      ('VIDEO', _SCRIPT_PATH / os.getenv('FILONOV_VIDEO_PATH')),
      ('YOUTUBE_VIDEO', _SCRIPT_PATH / os.getenv('FILONOV_YOUTUBE_LINK')),
    ],
  )
  def test_tag(self, media_type, media_location):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type=media_type,
      media_paths=[str(media_location)],
    )
    response = client.post('/media_tagging/tag', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_200_OK

    result = media_tagging.tagging_result.TaggingResult(
      **response.json().get('results')[0]
    )
    medium = media.Medium(media_path=media_location, media_type=media_type)
    assert result.identifier == medium.name
    assert result.output == 'tag'
    assert result.type == media_type.lower()
    assert result.tagger == self.tagger
    assert isinstance(result.content[0], media_tagging.tagging_result.Tag)

  @pytest.mark.parametrize(
    ('media_type', 'media_location'),
    [
      ('TEXT', filonov_test_text),
      ('IMAGE', _SCRIPT_PATH / os.getenv('FILONOV_IMAGE_PATH')),
      ('VIDEO', _SCRIPT_PATH / os.getenv('FILONOV_VIDEO_PATH')),
      ('YOUTUBE_VIDEO', _SCRIPT_PATH / os.getenv('FILONOV_YOUTUBE_LINK')),
    ],
  )
  def test_describe(self, media_type, media_location):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type=media_type,
      media_paths=[str(media_location)],
    )
    response = client.post('/media_tagging/describe', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_200_OK

    result = media_tagging.tagging_result.TaggingResult(
      **response.json().get('results')[0]
    )

    medium = media.Medium(media_path=media_location, media_type=media_type)
    assert result.identifier == medium.name
    assert result.type == media_type.lower()
    assert result.tagger == self.tagger
    assert isinstance(result.content, media_tagging.tagging_result.Description)


class TestGoogleCloudTagger:
  tagger = 'google-cloud'

  @pytest.mark.parametrize(
    ('media_type', 'media_location', 'expected_return_code'),
    [
      ('TEXT', filonov_test_text, fastapi.status.HTTP_404_NOT_FOUND),
      (
        'IMAGE',
        _SCRIPT_PATH / os.getenv('FILONOV_IMAGE_PATH'),
        fastapi.status.HTTP_200_OK,
      ),
      (
        'VIDEO',
        _SCRIPT_PATH / os.getenv('FILONOV_VIDEO_PATH'),
        fastapi.status.HTTP_200_OK,
      ),
      (
        'YOUTUBE_VIDEO',
        _SCRIPT_PATH / os.getenv('FILONOV_YOUTUBE_LINK'),
        fastapi.status.HTTP_404_NOT_FOUND,
      ),
    ],
  )
  def test_tag(self, media_type, media_location, expected_return_code):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type=media_type,
      media_paths=[str(media_location)],
    )
    response = client.post('/media_tagging/tag', json=request.model_dump())
    assert response.status_code == expected_return_code
    if expected_return_code == fastapi.status.HTTP_404_NOT_FOUND:
      return

    result = media_tagging.tagging_result.TaggingResult(
      **response.json().get('results')[0]
    )

    medium = media.Medium(media_path=media_location, media_type=media_type)
    assert result.identifier == medium.name
    assert result.type == media_type.lower()
    assert result.output == 'tag'
    assert result.tagger == self.tagger
    assert isinstance(result.content[0], media_tagging.tagging_result.Tag)

  @pytest.mark.parametrize(
    ('media_type', 'media_location', 'error'),
    [
      (
        'TEXT',
        filonov_test_text,
        'no supported tagging strategy for media type: TEXT',
      ),
      (
        'IMAGE',
        _SCRIPT_PATH / os.getenv('FILONOV_IMAGE_PATH'),
        'describe method is not supported',
      ),
      (
        'VIDEO',
        _SCRIPT_PATH / os.getenv('FILONOV_VIDEO_PATH'),
        'describe method is not supported',
      ),
      (
        'YOUTUBE_VIDEO',
        _SCRIPT_PATH / os.getenv('FILONOV_YOUTUBE_LINK'),
        'no supported tagging strategy for media type: YOUTUBE_VIDEO',
      ),
    ],
  )
  def test_describe(self, media_type, media_location, error):
    request = media_tagging.MediaTaggingRequest(
      tagger_type=self.tagger,
      media_type=media_type,
      media_paths=[str(media_location)],
    )
    response = client.post('/media_tagging/describe', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_404_NOT_FOUND
    assert error in response.json().get('detail')
