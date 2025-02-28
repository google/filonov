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
"""Module for performing media tagging with LLMs."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
from typing import Final

from typing_extensions import override

from media_tagging import media
from media_tagging.taggers import base
from media_tagging.taggers.llm.gemini import tagging_strategies as ts

DEFAULT_GEMINI_MODEL: Final[str] = 'models/gemini-2.0-flash'


class GeminiTagger(base.BaseTagger):
  """Tags media via Gemini."""

  alias = 'gemini'

  @override
  def __init__(
    self,
    model_name: str = DEFAULT_GEMINI_MODEL,
    **kwargs: str,
  ) -> None:
    """Initializes GeminiTagger based on model name."""
    self.model_name = model_name
    self.kwargs = kwargs
    super().__init__()

  @override
  def create_tagging_strategy(
    self, media_type: media.MediaTypeEnum
  ) -> base.TaggingStrategy:
    if media_type == media.MediaTypeEnum.IMAGE:
      return ts.ImageTaggingStrategy(self.model_name)
    if media_type == media.MediaTypeEnum.VIDEO:
      return ts.VideoTaggingStrategy(self.model_name)
    if media_type == media.MediaTypeEnum.YOUTUBE_VIDEO:
      return ts.YouTubeVideoTaggingStrategy(self.model_name)
    raise base.TaggerError(
      f'There are no supported taggers for media type: {media_type.name}'
    )
