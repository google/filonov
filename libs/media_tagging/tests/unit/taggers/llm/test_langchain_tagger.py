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

import json
from collections.abc import Sequence

import media_tagging.taggers.llm.langchain_tagger as tagger
import pytest
from langchain_core import language_models
from media_tagging import media, tagging_result
from media_tagging.taggers import base

_TAGS_RESPONSE = [
  {'name': 'test', 'score': 1.0},
  {'name': 'test2', 'score': 1.0},
  {'name': 'test3', 'score': 1.0},
]


def _build_tags_from_dicts(
  raw_tags: Sequence[dict[str, str]],
) -> tuple[tagging_result.Tag, ...]:
  return tuple(tagging_result.Tag(**raw_tag) for raw_tag in raw_tags)


class TestLangchainLLMTagger:
  @pytest.mark.parametrize(
    ('media_type', 'media_type_enum'),
    [
      ('image', media.MediaTypeEnum.IMAGE),
      ('video', media.MediaTypeEnum.VIDEO),
    ],
  )
  def test_tag_returns_correct_tagging_result_with_tags(
    self, mocker, media_type, media_type_enum
  ):
    medium = media.Medium('test', media_type_enum)
    mocker.patch(
      'media_tagging.media.Medium.content',
      new_callable=mocker.PropertyMock,
      return_value=bytes(),
    )
    test_tagger = tagger.LangchainLLMTagger(
      llm=language_models.FakeListChatModel(
        responses=[json.dumps([_TAGS_RESPONSE[0]])]
      ),
    )
    result = test_tagger.tag(medium, base.TaggingOptions(n_tags=100))

    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type=media_type,
      tagger='langchain',
      output='tag',
      content=_build_tags_from_dicts(_TAGS_RESPONSE[0:1]),
      tagging_details={'n_tags': 100},
    )

    assert result == expected_result

  @pytest.mark.parametrize(
    ('media_type', 'media_type_enum'),
    [
      ('image', media.MediaTypeEnum.IMAGE),
      ('video', media.MediaTypeEnum.VIDEO),
    ],
  )
  def test_tag_returns_correct_tagging_result_with_description(
    self, mocker, media_type, media_type_enum
  ):
    medium = media.Medium('test', media_type_enum)
    mocker.patch(
      'media_tagging.media.Medium.content',
      new_callable=mocker.PropertyMock,
      return_value=bytes(),
    )
    test_description = 'This is a test description'
    test_tagger = tagger.LangchainLLMTagger(
      llm=language_models.FakeListChatModel(
        responses=[json.dumps({'text': test_description})]
      ),
    )

    result = test_tagger.describe(
      medium, base.TaggingOptions(custom_prompt='Test custom prompt')
    )

    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type=media_type,
      tagger='langchain',
      output='description',
      content=tagging_result.Description(text=test_description),
      tagging_details={'custom_prompt': 'Test custom prompt'},
    )

    assert result == expected_result

  def test_tag_raises_tagger_error_on_unsupported_media_type(self):
    media_type = media.MediaTypeEnum.YOUTUBE_VIDEO
    test_description = 'This is a test description'
    test_tagger = tagger.LangchainLLMTagger(
      llm=language_models.FakeListChatModel(
        responses=[json.dumps({'text': test_description})]
      ),
    )
    with pytest.raises(base.TaggerError):
      test_tagger.tag(media.Medium('test', media_type))
