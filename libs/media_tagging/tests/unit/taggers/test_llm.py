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

import dataclasses
import json
from collections.abc import Sequence

import pytest
from media_tagging import media, tagging_result
from media_tagging.taggers import base, llm

_TAGS_RESPONSE = [
  {'name': 'test', 'score': 1.0},
  {'name': 'test2', 'score': 1.0},
  {'name': 'test3', 'score': 1.0},
]

medium = media.Medium('test')


def _build_tags_from_dicts(
  raw_tags: Sequence[dict[str, str]],
) -> list[tagging_result.Tag]:
  return [tagging_result.Tag(**raw_tag) for raw_tag in raw_tags]


def _build_tags_from_scores(
  tag_scores: dict[str, str],
) -> list[tagging_result.Tag]:
  return [
    tagging_result.Tag(name=name, score=score)
    for name, score in tag_scores.items()
  ]


@dataclasses.dataclass
class FakeTagsLangchainChainResponse:
  content: str
  usage_metadata: dict[str, int]


class FakeTagsLangchainChain:
  """Simulates langchain chain object for Tag output."""

  def invoke(self, parameters: dict[str, str]) -> list[dict[str, str]]:
    """Fake function for invoking llm."""
    if n_tags := parameters.get('n_tags'):
      return FakeTagsLangchainChainResponse(
        content=json.dumps(_TAGS_RESPONSE[0:n_tags]), usage_metadata={}
      )
    if tags := set(parameters.get('tags', '').split(',')):
      found_tags = []
      for tag in _TAGS_RESPONSE:
        if tag.get('name') in tags:
          tags.remove(tag.get('name'))
          found_tags.append(tag)
      found_tags += [{'name': tag.strip(), 'score': 0.0} for tag in tags]
      return FakeTagsLangchainChainResponse(
        content=json.dumps(found_tags), usage_metadata={}
      )
    return FakeTagsLangchainChainResponse(
      content=json.dumps(_TAGS_RESPONSE), usage_metadata={}
    )


class FakeDescriptionLangchainChain:
  """Simulates langchain chain object for Description output."""

  def invoke(self, parameters: dict[str, str]) -> dict[str, str]:
    """Fake function for invoking llm."""
    response_description = 'Test description.'
    if description_length := parameters.get('description_length'):
      response_description = response_description[0:description_length]
    return FakeTagsLangchainChainResponse(
      content=json.dumps({'text': response_description}), usage_metadata={}
    )


class TestGeminiImageTagger:
  @pytest.fixture
  def fake_tagger(self, mocker):
    mocker.patch(
      'media_tagging.taggers.llm.LLMTagger.chain',
      new_callable=mocker.PropertyMock,
      return_value=FakeTagsLangchainChain(),
    )
    return llm.GeminiImageTagger(llm.LLMTaggerTypeEnum.UNSTRUCTURED)

  def test_tag_with_custom_prompt_uses_it(self, mocker):
    mocker.patch(
      'media_tagging.taggers.llm.LLMTagger.chain',
      new_callable=mocker.PropertyMock,
      return_value=FakeTagsLangchainChain(),
    )
    fake_tagger = llm.GeminiImageTagger(llm.LLMTaggerTypeEnum.UNSTRUCTURED)
    custom_prompt = 'What are the colors in this image'
    fake_tagger.tag(
      medium,
      tagging_options=base.TaggingOptions(custom_prompt=custom_prompt),
    )
    assert fake_tagger.prompt == llm._build_prompt_template(custom_prompt)

  @pytest.mark.parametrize(
    ('n_tags', 'tags'),
    [
      (1, _TAGS_RESPONSE[0:1]),
      (2, _TAGS_RESPONSE[0:2]),
      (3, _TAGS_RESPONSE[0:3]),
      (4, _TAGS_RESPONSE[0:4]),
    ],
  )
  def test_tag_returns_correct_tagging_result_for_unstructured_tagger(
    self, mocker, n_tags, tags
  ):
    mocker.patch(
      'media_tagging.taggers.llm.LLMTagger.chain',
      new_callable=mocker.PropertyMock,
      return_value=FakeTagsLangchainChain(),
    )
    fake_tagger = llm.GeminiImageTagger(llm.LLMTaggerTypeEnum.UNSTRUCTURED)
    result = fake_tagger.tag(
      medium, tagging_options=base.TaggingOptions(n_tags=n_tags)
    )

    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='image',
      content=_build_tags_from_dicts(tags),
    )

    assert result == expected_result

  @pytest.mark.parametrize(
    ('tags', 'expected_tag_scores'),
    [
      ('test', {'test': 1.0}),
      ('test,not_found_tag', {'test': 1.0, 'not_found_tag': 0.0}),
    ],
  )
  def test_tag_returns_correct_tagging_result_for_structured_tagger(
    self, mocker, tags, expected_tag_scores
  ):
    mocker.patch(
      'media_tagging.taggers.llm.LLMTagger.chain',
      new_callable=mocker.PropertyMock,
      return_value=FakeTagsLangchainChain(),
    )
    fake_tagger = llm.GeminiImageTagger(llm.LLMTaggerTypeEnum.STRUCTURED)
    result = fake_tagger.tag(
      medium, tagging_options=base.TaggingOptions(tags=tags)
    )

    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='image',
      content=_build_tags_from_scores(expected_tag_scores),
    )

    assert result == expected_result

  def test_tag_returns_correct_tagging_result_for_description_tagger(
    self, mocker
  ):
    mocker.patch(
      'media_tagging.taggers.llm.LLMTagger.chain',
      new_callable=mocker.PropertyMock,
      return_value=FakeDescriptionLangchainChain(),
    )
    fake_tagger = llm.GeminiImageTagger(llm.LLMTaggerTypeEnum.DESCRIPTION)
    result = fake_tagger.tag(medium)

    expected_result = tagging_result.TaggingResult(
      identifier='test',
      type='image',
      content=tagging_result.Description(text='Test description.'),
    )

    assert result == expected_result


class TestGeminiYouTubeTagger:
  def test_format_prompt_with_custom_prompt_uses_it(self):
    fake_tagger = llm.GeminiYouTubeVideoTagger(
      llm.LLMTaggerTypeEnum.UNSTRUCTURED
    )
    custom_prompt = 'What are the colors in this video'
    generated_prompt = fake_tagger.format_prompt(
      tagging_options=base.TaggingOptions(custom_prompt=custom_prompt)
    )
    assert generated_prompt == custom_prompt

  def test_format_prompt_without_custom_prompt_uses_default_prompt(self):
    fake_tagger = llm.GeminiYouTubeVideoTagger(
      llm.LLMTaggerTypeEnum.UNSTRUCTURED
    )
    generated_prompt = fake_tagger.format_prompt(
      tagging_options=base.TaggingOptions(n_tags=10)
    )
    expected_prompt = (
      llm.video_llm_tagger_promps[llm.LLMTaggerTypeEnum.UNSTRUCTURED].format(
        n_tags=10
      )
      + llm.TAG_DESCRIPTION
    )
    assert generated_prompt == expected_prompt
