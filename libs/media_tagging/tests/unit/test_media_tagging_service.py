# Copyright 2024 Google LLC
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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-module-docstring, missing-class-docstring, missing-function-docstring

import hashlib

import pydantic
import pytest
from media_tagging import (
  media_tagging_service,
  tagging_result,
)


class FakeLLMResponse(pydantic.BaseModel):
  text: str


FAKE_TAGS = [tagging_result.Tag(name=f'fake_{i}', score=1.0) for i in range(10)]


class TestMediaTaggingService:
  @pytest.fixture
  def service(self):
    return media_tagging_service.MediaTaggingService()

  def test_describe_media_returns_correct_tagging_result(self, service):
    n_runs = 5
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      tagger='fake',
      output='description',
      type='text',
      content=tagging_result.Description(text='fake'),
      tagging_details={'n_runs': n_runs},
      hash=hashlib.md5(b'test').hexdigest(),
    )
    test_tagging_result = service.describe_media(
      media_tagging_service.MediaTaggingRequest(
        tagger_type='fake',
        media_type='TEXT',
        media_paths=['test'],
        parallel_threshold=0,
        tagging_options={'n_runs': 5},
      )
    )

    expected_response = media_tagging_service.MediaTaggingResponse(
      results=[expected_result] * n_runs
    )

    assert test_tagging_result == expected_response

  def test_tag_media_returns_correct_tagging_result(self, service):
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      tagger='fake',
      output='tag',
      type='text',
      content=FAKE_TAGS,
      hash=hashlib.md5(b'test').hexdigest(),
    )
    test_tagging_result = service.tag_media(
      media_tagging_service.MediaTaggingRequest(
        tagger_type='fake',
        media_type='TEXT',
        media_paths=['test'],
        parallel_threshold=0,
      )
    )

    assert test_tagging_result == media_tagging_service.MediaTaggingResponse(
      results=[expected_result]
    )

  def test_tag_media_returns_correct_tagging_result_for_different_tagging_details(
    self, service
  ):
    service.tag_media(
      media_tagging_service.MediaTaggingRequest(
        tagger_type='fake',
        media_type='TEXT',
        media_paths=['test'],
        parallel_threshold=0,
        tagging_options={'n_tags': 5},
      )
    )
    test_tagging_result = service.tag_media(
      media_tagging_service.MediaTaggingRequest(
        tagger_type='fake',
        media_type='TEXT',
        media_paths=['test'],
        parallel_threshold=0,
        tagging_options={'n_tags': 10},
      )
    )
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      tagger='fake',
      output='tag',
      type='text',
      content=FAKE_TAGS,
      tagging_details={'n_tags': 10},
      hash=hashlib.md5(b'test').hexdigest(),
    )
    assert test_tagging_result == media_tagging_service.MediaTaggingResponse(
      results=[expected_result]
    )
