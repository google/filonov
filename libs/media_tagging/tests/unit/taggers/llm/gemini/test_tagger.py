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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-module-docstring, missing-class-docstring, missing-function-docstring

import pytest
from media_tagging import media
from media_tagging.taggers.llm.gemini import tagger


class TestGeminiTagger:
  @pytest.mark.parametrize(
    ('model_name', 'expected_model'),
    [
      ('gemini-2.5', 'models/gemini-2.5'),
      ('models/gemini-2.5', 'models/gemini-2.5'),
      (None, tagger.DEFAULT_GEMINI_MODEL),
    ],
  )
  def test_init_tagger_returns_correct_model(self, model_name, expected_model):
    test_tagger = tagger.GeminiTagger(model_name=model_name)
    assert test_tagger.model_name == expected_model

  def test_init_tagger_from_kwargs_returns_correct_model(self):
    tagger_parameters = {'model': 'gemini-2.5'}
    test_tagger = tagger.GeminiTagger(**tagger_parameters)
    assert test_tagger.model_name == 'models/gemini-2.5'

  def test_create_tagging_strategy_raises_error_on_incorrect_media_type(
    self,
  ):
    test_tagger = tagger.GeminiTagger()
    with pytest.raises(
      tagger.GeminiTaggerError,
      match='There are no supported taggers for media type: UNKNOWN',
    ):
      test_tagger.create_tagging_strategy(media.MediaTypeEnum.UNKNOWN)

  def test_create_tagging_strategy_raises_error_on_model_media_mismatch(
    self,
  ):
    test_tagger = tagger.GeminiTagger()
    with pytest.raises(
      tagger.GeminiTaggerError,
      match='Working with WEBPAGE media type works with gemini-2.5 models only',
    ):
      test_tagger.create_tagging_strategy(media.MediaTypeEnum.WEBPAGE)
