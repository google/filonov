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
"""Module for performing media tagging with LLMs."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import base64
import logging
from typing import Final

from langchain_core import (
  language_models,
  output_parsers,
  prompts,
  runnables,
)
from typing_extensions import override

from media_tagging import media, tagging_result
from media_tagging.taggers import base
from media_tagging.taggers.llm import utils

MAX_NUMBER_LLM_TAGS: Final[int] = 10


class LLMTaggingStrategy(base.TaggingStrategy):
  """Defines LLM specific tagging strategy.

  Attributes:
    chain: Langchain chain.
  """

  def __init__(
    self,
    llm: language_models.BaseLanguageModel,
  ) -> None:
    """Initializes LLMTaggingStrategy based on selected LLM."""
    self.llm = llm
    self._prompt = None
    self._chain = None
    self.include_media_data_in_prompt = True

  def get_chain(
    self,
    output: tagging_result.TaggingOutput,
    include_media_data: bool,
    custom_prompt: str,
  ) -> runnables.base.RunnableSequence:  # noqa: D102
    if not self._chain:
      prompt = self.get_prompt(output, include_media_data, custom_prompt)
      self._chain = prompt | self.llm
    return self._chain

  def get_prompt(
    self,
    output: tagging_result.TaggingOutput,
    include_media_data: bool,
    custom_prompt: str,
  ) -> prompts.ChatPromptTemplate:
    """Builds correct prompt to send to LLM."""
    if custom_prompt:
      return _build_prompt_template(custom_prompt, include_media_data)
    prompt_file_name = 'tag' if output == tagging_result.Tag else 'description'
    return _build_prompt_template(
      utils.read_prompt_content(prompt_file_name), include_media_data
    )

  def convert_medium_to_encoded_string(self, medium) -> str:
    """Helper method for converting medium content to a string."""
    return base64.b64encode(medium.content).decode('utf-8')

  def get_llm_response(
    self,
    medium: media.Medium,
    parser: output_parsers.JsonOutputParser,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    """Defines how to interact with LLM to perform media tagging.

    Args:
      medium: Instantiated media object.
      output: Type of output to request from LLM.
      tagging_options: Additional parameters to fine-tune tagging.

    Returns:
      Formatted LLM response.
    """
    if not tagging_options:
      tagging_options = base.TaggingOptions(n_tags=MAX_NUMBER_LLM_TAGS)
    if custom_prompt := tagging_options.custom_prompt:
      self.custom_prompt = custom_prompt

    logging.debug(
      'Tagging %s "%s" with LLMTagger', medium.type.name, medium.name
    )
    image_data = self.convert_medium_to_encoded_string(medium)
    chain = self.get_chain(
      parser.pydantic_object,
      include_media_data=True,
      custom_prompt=tagging_options.custom_prompt,
    )
    response = chain.invoke(
      utils.get_invocation_parameters(
        media_type=medium.type.name,
        format_instructions=parser.get_format_instructions(),
        tagging_options=tagging_options,
        image_data=image_data,
      )
    )
    if hasattr(response, 'usage_metadata'):
      logging.debug(
        'usage_metadata for media %s: %s',
        medium.name,
        response.usage_metadata,
      )
    return parser.parse(response.content)

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(
      n_tags=MAX_NUMBER_LLM_TAGS
    ),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    parser = output_parsers.JsonOutputParser(pydantic_object=tagging_result.Tag)
    result = self.get_llm_response(medium, parser, tagging_options)
    if 'tags' in result:
      result = result.get('tags')
    tags = [
      tagging_result.Tag(name=r.get('name'), score=r.get('score'))
      for r in result
    ]
    return tagging_result.TaggingResult(
      identifier=medium.name, type=medium.type.name.lower(), content=tags
    )

  @override
  def describe(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    parser = output_parsers.JsonOutputParser(
      pydantic_object=tagging_result.Description
    )
    result = self.get_llm_response(medium, parser, tagging_options)
    description = result.get('text')
    return tagging_result.TaggingResult(
      identifier=medium.name,
      type=medium.type.name.lower(),
      content=tagging_result.Description(text=description),
    )


class ImageTaggingStrategy(LLMTaggingStrategy):
  """Tags image via LLM."""


class VideoTaggingStrategy(LLMTaggingStrategy):
  """Tags video via LLM."""


def _build_prompt_template(
  prompt: str,
  include_image_data: bool = False,
) -> prompts.ChatPromptTemplate | str:
  """Constructs prompt template from file.

  Args:
    prompt: Text of a prompt.
    include_image_data: Whether to include image_urls in prompt.

  Returns:
    Generated prompt template.
  """
  system_prompt = ('system', 'You are a helpful assistant')
  user_input = [
    {
      'type': 'text',
      'text': prompt
      + 'Use the following formatting instructions: {format_instructions}',
    }
  ]
  if include_image_data:
    user_input.append(
      {
        'type': 'image_url',
        'image_url': {'url': 'data:image/jpeg;base64,{image_data}'},
      }
    )

  user_prompt = ('human', user_input)
  return prompts.ChatPromptTemplate.from_messages([system_prompt, user_prompt])
