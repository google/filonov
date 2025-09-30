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

import pytest
from media_tagging import media
from media_tagging.taggers.llm.gemini import tagging_strategies as ts


class TestGeminiTaggingStrategy:
  @pytest.fixture
  def strategy(self):
    return ts.TextTaggingStrategy(
      model_name='models/gemini-2.5-flash',
      model_parameters=ts.GeminiModelParameters(),
    )

  def test_tag_raises_error_for_webpage_type(self, strategy):
    medium = media.Medium(
      media_path='example.com', media_type=media.MediaTypeEnum.WEBPAGE
    )

    with pytest.raises(ts.GeminiTaggingError):
      strategy.tag(medium)
