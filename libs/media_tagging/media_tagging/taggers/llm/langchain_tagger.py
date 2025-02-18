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
import importlib
import inspect

from langchain_core import language_models
from typing_extensions import override

from media_tagging import media
from media_tagging.taggers import base
from media_tagging.taggers.llm import langchain_tagging_strategies as ts


def load_llm(full_path: str) -> type[language_models.BaseLanguageModel]:
  """Loads LLM based on a fully qualified format.

  Format of llm_path should be similar to
  `langchain_google_genai.ChatGoogleGenerativeAI` (the corresponding
  library should be installed).

  Args:
    full_path: Fully qualified name of class in a library.

  Returns:
    LLM class.

  Raises:
    ValueError: If library is not installed or doesn't contains requested class.
  """
  *langchain_module_path, langchain_class = full_path.split('.')
  try:
    llm_module = importlib.import_module('.'.join(langchain_module_path))
  except ModuleNotFoundError as e:
    raise ValueError(
      f'Library {langchain_module_path[0]} is not installed'
    ) from e
  for object_name, obj in inspect.getmembers(llm_module):
    if (
      inspect.isclass(obj)
      and issubclass(obj, language_models.BaseLanguageModel)
      and object_name == langchain_class
    ):
      return obj
  raise ValueError(f'Failed to find class {langchain_class}')


class LangchainLLMTagger(base.BaseTagger):
  """Tags media via one of supported multimodal LLMs available via Langchain."""

  alias = 'langchain'

  def __init__(
    self,
    llm: language_models.BaseLanguageModel | None = None,
    llm_class_name: str | None = None,
    **kwargs: str,
  ) -> None:
    """Initializes LangchainLLMTagger based on type of selected LLM.

    Args:
      llm: Initialized LLM.
      llm_class_name: Fully qualified name of LLM in langchain library.

    """
    if not llm and not llm_class_name:
      raise ValueError(
        'Either provide llm_class_name or instantiated LLM in constructor'
      )
    self._llm = llm
    self._llm_class_name = llm_class_name
    self.kwargs = kwargs
    super().__init__()

  @property
  def llm(self) -> language_models.BaseLanguageModel:
    """Initialized LLM.

    If no LLM was provided in constructor tries to load one.
    """
    if not self._llm:
      self._llm = load_llm(self._llm_class_name)(**self.kwargs)
    return self._llm

  @override
  def create_tagging_strategy(
    self, media_type: media.MediaTypeEnum
  ) -> base.TaggingStrategy:
    if media_type == media.MediaTypeEnum.IMAGE:
      return ts.ImageTaggingStrategy(self.llm)
    if media_type == media.MediaTypeEnum.VIDEO:
      return ts.VideoTaggingStrategy(self.llm)
    raise base.TaggerError(
      f'There are no supported taggers for media type: {media_type.name}'
    )
