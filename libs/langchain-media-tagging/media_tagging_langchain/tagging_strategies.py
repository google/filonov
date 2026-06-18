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
"""Performs media tagging with Langchain supported LLMs."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import base64
import pathlib
from typing import Final

import pydantic
from langchain_core import (
  language_models,
  prompts,
)
from media_tagging import media, tagging_result
from media_tagging.taggers import base
from media_tagging.taggers.llm import utils as media_tagging_llm_utils
from typing_extensions import override

MAX_NUMBER_LLM_TAGS: Final[int] = 10


class Tags(pydantic.BaseModel):
  content: list[tagging_result.Tag]


class Descriptions(pydantic.BaseModel):
  content: list[tagging_result.Description]


class LLMTaggingStrategy(base.TaggingStrategy):
  """Defines Langchain specific tagging strategy."""

  def __init__(
    self, llm: language_models.BaseLanguageModel, **kwargs: str
  ) -> None:
    """Initializes LLMTaggingStrategy based on selected LLM."""
    self.llm = llm
    self._prompt = None

  def build_content(self, medium: media.Medium, **kwargs):
    """Convert media to a format usable by LLM."""
    raise NotImplementedError

  def build_prompt(
    self,
    medium: media.Medium,
    output: tagging_result.TaggingOutput,
    tagging_options: base.TaggingOptions,
  ) -> str:
    """Builds correct prompt based on medium and tagging options."""
    if self._prompt:
      return self._prompt
    include_media_data = (
      bool(medium.media_path) and pathlib.Path(medium.media_path).is_file()
    )
    if custom_prompt := tagging_options.custom_prompt:
      self._prompt = _build_prompt_template(
        media_type=medium.type,
        prompt=custom_prompt,
        include_image_data=include_media_data,
      )
      return self._prompt
    prompt_file_name = 'tag' if output == tagging_result.Tag else 'description'
    prompt = media_tagging_llm_utils.read_prompt_content(prompt_file_name)
    parameters = media_tagging_llm_utils.get_invocation_parameters(
      media_type=medium.type.name,
      tagging_options=tagging_options,
    )
    prompt = prompt.format(**parameters)
    self._prompt = _build_prompt_template(
      media_type=medium.type,
      prompt=prompt,
      include_image_data=include_media_data,
    )
    return self._prompt

  def _process_medium(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions,
    output: tagging_result.TaggingOutput,
    output_schema: pydantic.BaseModel,
  ):
    prompt = self.build_prompt(
      medium=medium,
      output=output,
      tagging_options=tagging_options,
    )
    medium_content = self.build_content(medium)
    result = (
      prompt | self.llm.with_structured_output(schema=output_schema)
    ).invoke({'medium_content': medium_content})
    return tagging_result.TaggingResult(
      identifier=medium.name,
      type=medium.type.name.lower(),
      content=result.content,
      hash=medium.identifier,
    )

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(
      n_tags=MAX_NUMBER_LLM_TAGS
    ),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    if not tagging_options:
      tagging_options.n_tags = MAX_NUMBER_LLM_TAGS
    return self._process_medium(
      medium, tagging_options, output=tagging_result.Tag, output_schema=Tags
    )

  @override
  def describe(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    return self._process_medium(
      medium,
      tagging_options,
      output=tagging_result.Description,
      output_schema=Descriptions,
    )


class TextTaggingStrategy(LLMTaggingStrategy):
  """Tags texts via LLM."""

  def build_content(self, medium, **kwargs):
    return str(medium.content)


class ImageTaggingStrategy(LLMTaggingStrategy):
  """Tags images via LLM."""

  def build_content(self, medium, **kwargs):
    if medium.media_path and pathlib.Path(medium.media_path).is_file():
      return base64.b64encode(medium.content).decode('utf-8')
    return medium.media_path


class VideoTaggingStrategy(LLMTaggingStrategy):
  """Tags videos via LLM."""

  def build_content(self, medium, **kwargs):
    return str(medium.content)


def _build_prompt_template(
  media_type: str,
  prompt: str,
  include_image_data: bool = False,
) -> prompts.ChatPromptTemplate | str:
  """Constructs prompt template from file.

  Args:
    media_type: Type of media to process.
    prompt: Text of a prompt.
    include_image_data: Whether to include image_urls in prompt.

  Returns:
    Generated prompt template.
  """
  system_prompt = ('system', 'You are a helpful assistant')
  user_input = [{'type': 'text', 'text': prompt}]
  if include_image_data:
    medium_content = 'data:image/jpeg;base64,{medium_content}'
  else:
    medium_content = '{medium_content}'

  if media_type == 'IMAGE':
    user_input.append(
      {
        'type': 'image_url',
        'image_url': {'url': medium_content},
      }
    )
  elif media_type == 'TEXT':
    user_input.append(
      {
        'type': 'image_url',
        'text': medium_content,
      }
    )

  user_prompt = ('human', user_input)
  return prompts.ChatPromptTemplate.from_messages([system_prompt, user_prompt])
