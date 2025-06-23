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
  def __init__(self, model_name: str | None = None, **kwargs: str) -> None:
    """Initializes GeminiTagger based on model name."""
    self.model_name = self._format_model_name(model_name or kwargs.get('model'))
    self.model_parameters = ts.GeminiModelParameters(**kwargs)
    super().__init__()

  def _format_model_name(self, model_name: str | None) -> str:
    if model_name:
      return (
        model_name
        if model_name.startswith('models/')
        else f'models/{model_name}'
      )
    return DEFAULT_GEMINI_MODEL

  @override
  def create_tagging_strategy(
    self, media_type: media.MediaTypeEnum
  ) -> base.TaggingStrategy:
    tagging_strategies = {
      media.MediaTypeEnum.IMAGE: ts.ImageTaggingStrategy,
      media.MediaTypeEnum.VIDEO: ts.VideoTaggingStrategy,
      media.MediaTypeEnum.YOUTUBE_VIDEO: ts.YouTubeVideoTaggingStrategy,
    }
    if not (tagging_strategy := tagging_strategies.get(media_type)):
      raise base.TaggerError(
        f'There are no supported taggers for media type: {media_type.name}'
      )
    return tagging_strategy(self.model_name, self.model_parameters)
