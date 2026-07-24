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

from google import genai
from media_tagging import media
from media_tagging.taggers import base
from media_tagging.taggers.llm.gemini import tagging_strategies as ts


def test_build_prompt_config():
  prompt = ts.build_prompt_config(
    medium=media.Medium(media_path='test', media_type='TEXT'),
    tagging_options=base.TaggingOptions(
      safety_settings=[{'harm_category_hate_speech': 'off'}]
    ),
  )
  expected_safety_settings = [
    genai.types.SafetySetting(
      category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
      threshold=genai.types.HarmBlockThreshold.OFF,
    ),
  ]

  assert prompt.safety_settings == expected_safety_settings
