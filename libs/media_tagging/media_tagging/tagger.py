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
"""Module for performing media tagging.

Media tagging sends API requests to tagging engine (i.e. Google Vision API)
and returns tagging results that can be easily written.
"""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
from typing import Final

from media_tagging.taggers import api, base, llm

TAGGERS = {
  'vision-api': api.GoogleVisionAPITagger,
  'video-api': api.GoogleVideoIntelligenceAPITagger,
  'gemini-image': llm.GeminiImageTagger,
  'gemini-structured-image': llm.GeminiImageTagger,
  'gemini-description-image': llm.GeminiImageTagger,
  'gemini-video': llm.GeminiVideoTagger,
  'gemini-structured-video': llm.GeminiVideoTagger,
  'gemini-description-video': llm.GeminiVideoTagger,
  'gemini-youtube-video': llm.GeminiYouTubeVideoTagger,
  'gemini-structured-youtube-video': llm.GeminiYouTubeVideoTagger,
  'gemini-description-youtube-video': llm.GeminiYouTubeVideoTagger,
}

_LLM_TAGGERS_TYPES = {
  'gemini-image': llm.LLMTaggerTypeEnum.UNSTRUCTURED,
  'gemini-structured-image': llm.LLMTaggerTypeEnum.STRUCTURED,
  'gemini-description-image': llm.LLMTaggerTypeEnum.DESCRIPTION,
  'gemini-video': llm.LLMTaggerTypeEnum.UNSTRUCTURED,
  'gemini-structured-video': llm.LLMTaggerTypeEnum.STRUCTURED,
  'gemini-description-video': llm.LLMTaggerTypeEnum.DESCRIPTION,
  'gemini-youtube-video': llm.LLMTaggerTypeEnum.UNSTRUCTURED,
  'gemini-structured-youtube-video': llm.LLMTaggerTypeEnum.STRUCTURED,
  'gemini-description-youtube-video': llm.LLMTaggerTypeEnum.DESCRIPTION,
}

MEDIA_TAGGER_DESCRIPTION: Final[str] = f"""
  Helps to analyze content of images and videos with APIs and Large language
  models. Several taggers are available -
  {list(TAGGERS.keys())}
  When URL is provided it's always treated as 'media_url' parameter.
"""


def create_tagger(
  tagger_type: str, tagger_parameters: dict[str, str] | None = None
) -> base.BaseTagger:
  """Factory for creating taggers based on provided type.

  Args:
    tagger_type: Type of tagger.
    tagger_parameters: Various parameters to instantiate tagger.

  Returns:
    Concrete tagger class.
  """
  if not tagger_parameters:
    tagger_parameters = {}
  if tagger := TAGGERS.get(tagger_type):
    if issubclass(tagger, llm.LLMTagger):
      return tagger(
        tagger_type=_LLM_TAGGERS_TYPES.get(tagger_type), **tagger_parameters
      )
    return tagger(**tagger_parameters)
  raise ValueError(
    f'Incorrect tagger "{tagger_type}" is provided, '
    f'valid options: {list(TAGGERS.keys())}'
  )
