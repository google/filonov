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
import json

import pydantic
import pytest
from media_tagging import (
  media_tagging_service,
  tagging_result,
)


class FakeLLMResponse(pydantic.BaseModel):
  text: str


class TestMediaTaggingService:
  @pytest.fixture
  def service(self):
    return media_tagging_service.MediaTaggingService()

  def test_describe_media_returns_correct_tagging_result(self, service, mocker):
    test_llm_response = FakeLLMResponse(
      text=json.dumps({'text': 'Test description.'})
    )
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      tagger='gemini',
      output='description',
      type='text',
      content=tagging_result.Description(text='Test description.'),
      hash=hashlib.md5(b'test').hexdigest(),
    )
    mocker.patch(
      'media_tagging.taggers.llm.gemini.tagging_strategies.GeminiTaggingStrategy.get_llm_response',
      return_value=test_llm_response,
    )
    test_tagging_result = service.describe_media(
      media_tagging_service.MediaTaggingRequest(
        tagger_type='gemini',
        media_type='TEXT',
        media_paths=['test'],
        parallel_threshold=0,
      )
    )

    assert test_tagging_result == media_tagging_service.MediaTaggingResponse(
      results=[expected_result]
    )

  def test_tag_media_returns_correct_tagging_result(self, service, mocker):
    test_llm_response = FakeLLMResponse(
      text=json.dumps([{'name': 'test', 'score': 0.5}])
    )
    expected_result = tagging_result.TaggingResult(
      identifier='test',
      tagger='gemini',
      output='tag',
      type='text',
      content=[tagging_result.Tag(name='test', score=0.5)],
      tagging_details={'n_tags': 10},
      hash=hashlib.md5(b'test').hexdigest(),
    )
    mocker.patch(
      'media_tagging.taggers.llm.gemini.tagging_strategies.GeminiTaggingStrategy.get_llm_response',
      return_value=test_llm_response,
    )
    test_tagging_result = service.tag_media(
      media_tagging_service.MediaTaggingRequest(
        tagger_type='gemini',
        media_type='TEXT',
        media_paths=['test'],
        parallel_threshold=0,
      )
    )

    assert test_tagging_result == media_tagging_service.MediaTaggingResponse(
      results=[expected_result]
    )
