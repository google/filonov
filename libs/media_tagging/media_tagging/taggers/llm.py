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
import base64
import dataclasses
import enum
import functools
import json
import logging
import pathlib
import tempfile
from typing import Final

import google.generativeai as google_genai
import langchain_google_genai as genai
import proto
import tenacity
from google.api_core import exceptions as google_api_exceptions
from langchain_core import (
  language_models,
  output_parsers,
  prompts,
  runnables,
)
from typing_extensions import override
from vertexai import generative_models as google_generative_models

from media_tagging import exceptions, media, tagging_result
from media_tagging.taggers import base

_MAX_NUMBER_LLM_TAGS: Final[int] = 10
_TAG_DESCRIPTION: Final[str] = """
  Tag represents a unique concept (using a singular noun).
  Each value is between 0 and 1 where 0 is complete absence of concept,
  1 is complete presence, and everything in between represents a degree of
  presence. Make sure that tags are lowercase and unique.
"""


def _build_prompt_template(
  prompt_name: str,
  include_human_instructions: bool = True,
  include_format_instructions: bool = True,
) -> str | prompts.ChatPromptTemplate:
  """Constructs prompt template from file.

  Args:
    prompt_name: File name with extension where prompt template is saved.
    include_human_instructions: Whether to include image_url in a prompt.
    include_format_instructions: Whether to specify output formatting.

  Returns:
    Generated prompt template.
  """
  with open(
    pathlib.Path(__file__).resolve().parent / prompt_name,
    'r',
    encoding='utf-8',
  ) as f:
    template = f.readlines()
  prompt_template = ' '.join(template)
  if include_format_instructions:
    prompt_template = prompt_template + '{format_instructions}'
  if include_human_instructions:
    human_instructions = (
      'human',
      [
        {
          'type': 'image_url',
          'image_url': {'url': 'data:image/jpeg;base64,{image_data}'},
        }
      ],
    )
    return prompts.ChatPromptTemplate.from_messages(
      [
        ('system', prompt_template),
        human_instructions,
      ]
    )
  return prompt_template


class LLMTaggerTypeEnum(enum.Enum):
  """Enum for selecting of type of LLM tagging."""

  STRUCTURED = 1
  UNSTRUCTURED = 2
  DESCRIPTION = 3


llm_tagger_promps: dict[LLMTaggerTypeEnum, prompts.ChatPromptTemplate] = {
  LLMTaggerTypeEnum.UNSTRUCTURED: _build_prompt_template(
    'image_unstructured_prompt_template.txt'
  ),
  LLMTaggerTypeEnum.STRUCTURED: _build_prompt_template(
    'image_structured_prompt_template.txt'
  ),
  LLMTaggerTypeEnum.DESCRIPTION: _build_prompt_template(
    'image_description_prompt_template.txt'
  ),
}

video_llm_tagger_promps: dict[LLMTaggerTypeEnum, str] = {
  LLMTaggerTypeEnum.UNSTRUCTURED: _build_prompt_template(
    'video_unstructured_prompt_template.txt',
    include_human_instructions=False,
    include_format_instructions=False,
  ),
  LLMTaggerTypeEnum.STRUCTURED: _build_prompt_template(
    'video_structured_prompt_template.txt',
    include_human_instructions=False,
    include_format_instructions=False,
  ),
  LLMTaggerTypeEnum.DESCRIPTION: _build_prompt_template(
    'video_description_prompt_template.txt',
    include_human_instructions=False,
    include_format_instructions=False,
  ),
}


class LLMTagger(base.BaseTagger):
  """Tags media via LLM."""

  def __init__(
    self,
    llm_tagger_type: LLMTaggerTypeEnum,
    llm: language_models.BaseLanguageModel,
  ) -> None:
    """Initializes LLMTagger based on selected LLM."""
    self.llm_tagger_type = llm_tagger_type
    self.llm = llm
    self.output_object = (
      tagging_result.Description
      if llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION
      else tagging_result.Tag
    )

  @property
  def prompt(self) -> prompts.ChatPromptTemplate:
    """Builds correct prompt to send to LLM.

    Prompt contains format instructions to get output result.
    """
    prompt = llm_tagger_promps[self.llm_tagger_type]
    if self.output_object == LLMTaggerTypeEnum.DESCRIPTION:
      return prompt
    return prompt + _TAG_DESCRIPTION

  @property
  def output_parser(self) -> output_parsers.BaseOutputParser:
    """Defines how LLM response should be formatted."""
    return output_parsers.JsonOutputParser(pydantic_object=self.output_object)

  @property
  def chain(self) -> runnables.base.RunnableSequence:  # noqa: D102
    return self.prompt | self.llm

  def invocation_parameters(
    self, image_data: str, tagging_options: base.TaggingOptions
  ) -> dict[str, str]:
    """Prepares necessary parameters for chain invocation.

    Args:
      image_data: Base64 encoded image.
      tagging_options: Parameters to refine the tagging results.

    Returns:
      Necessary parameters to be invoke by the chain.
    """
    parameters = {
      'image_data': image_data,
      'format_instructions': self.output_parser.get_format_instructions(),
    }
    if n_tags := tagging_options.n_tags:
      parameters['n_tags'] = n_tags
    if tags := tagging_options.tags:
      parameters['tags'] = ', '.join(tags)
    return parameters

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ) -> tagging_result.TaggingResult:
    if not tagging_options:
      tagging_options = base.TaggingOptions(n_tags=_MAX_NUMBER_LLM_TAGS)

    logging.debug('Tagging image "%s" with LLMTagger', medium.name)
    image_data = base64.b64encode(medium.content).decode('utf-8')
    response = self.chain.invoke(
      self.invocation_parameters(image_data, tagging_options)
    )
    logging.info(
      'usage_metadata for media %s: %s',
      medium.name,
      response.usage_metadata,
    )
    result = self.output_parser.parse(response.content)
    if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION:
      return tagging_result.TaggingResult(
        identifier=medium.name,
        type='image',
        content=tagging_result.Description(text=result.get('text')),
      )
    tags = [
      tagging_result.Tag(name=r.get('name'), score=r.get('score'))
      for r in result
    ]
    return tagging_result.TaggingResult(
      identifier=medium.name, type='image', content=tags
    )


class GeminiImageTagger(LLMTagger):
  """Tags image based on Gemini."""

  def __init__(
    self,
    tagger_type: LLMTaggerTypeEnum,
    model_name: str = 'models/gemini-1.5-flash',
  ) -> None:
    """Initializes GeminiImageTagger.

    Args:
      tagger_type: Type of LLM tagger.
      model_name: Name of the model to perform the tagging.
    """
    super().__init__(
      llm_tagger_type=tagger_type,
      llm=genai.ChatGoogleGenerativeAI(model=model_name),
    )


class GeminiYouTubeVideoTagger(LLMTagger):
  """Tags YouTube videos based on Gemini."""

  def __init__(
    self,
    tagger_type: LLMTaggerTypeEnum,
    model_name: str = 'models/gemini-1.5-flash',
  ) -> None:
    """Initializes GeminiYouTubeVideoTagger.

    Args:
      tagger_type: Type of LLM tagger.
      model_name: Name of the model to perform the tagging.
    """
    self.llm_tagger_type = tagger_type
    self.model_name = model_name

  @functools.cached_property
  def model(self) -> google_generative_models.GenerativeModel:
    """Initializes GenerativeModel."""
    return google_generative_models.GenerativeModel(model_name=self.model_name)

  @property
  def response_schema(self):
    """Generates correct response schema based on type of LLM tagger."""
    if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION:
      return {'type': 'object', 'properties': {'text': {'type': 'string'}}}
    return {
      'type': 'array',
      'items': {
        'type': 'object',
        'properties': {
          'name': {'type': 'STRING'},
          'score': {
            'type': 'NUMBER',
            'description': (
              'How prominent the tag from 0 to 1, '
              'where 0 is tag absent and 1 is complete tag present'
            ),
          },
        },
      },
    }

  def format_prompt(self, tagging_options: base.TaggingOptions) -> str:
    """Builds correct prompt to send to LLM.

    Prompt contains format instructions to get output result.

    Args:
      tagging_options: Parameters to refine the prompt.

    Returns:
      Formatted prompt.
    """
    base_prompt = video_llm_tagger_promps[self.llm_tagger_type]
    formatting_instructions = (
      ' For each tag provide name and a score from 0 to 1 '
      'where 0 is tag absence and 1 complete tag presence.'
    )
    prompt = base_prompt.format(**dataclasses.asdict(tagging_options))
    if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION:
      return prompt
    return prompt + formatting_instructions

  @override
  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(),
    retry=tenacity.retry_if_exception_type(json.decoder.JSONDecodeError),
    reraise=True,
  )
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    logging.debug(
      'Tagging video "%s" with GeminiYouTubeVideoTagger', medium.name
    )
    video_file = google_generative_models.Part.from_uri(
      uri=medium.media_path, mime_type='video/*'
    )
    try:
      result = self.model.generate_content(
        [
          video_file,
          '\n\n',
          f'{self.format_prompt(tagging_options)} ',
        ],
        generation_config=google_generative_models.GenerationConfig(
          response_mime_type='application/json',
          response_schema=self.response_schema,
        ),
      )
    except google_api_exceptions.PermissionDenied:
      return None
    if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION:
      return tagging_result.TaggingResult(
        identifier=medium.name,
        type='youtube_video',
        content=tagging_result.Description(
          text=json.loads(result.text).get('text')
        ),
      )

    tags = [
      tagging_result.Tag(name=r.get('name'), score=r.get('score'))
      for r in json.loads(result.text)
    ]
    logging.info(
      'usage_metadata for media %s: %s',
      medium.name,
      proto.Message.to_dict(result.usage_metadata),
    )
    return tagging_result.TaggingResult(
      identifier=medium.name, type='youtube_video', content=tags
    )


class GeminiVideoTagger(LLMTagger):
  """Tags video based on Gemini."""

  def __init__(
    self,
    tagger_type: LLMTaggerTypeEnum,
    model_name: str = 'models/gemini-1.5-flash',
  ) -> None:
    """Initializes GeminiVideoTagger.

    Args:
      tagger_type: Type of LLM tagger.
      model_name: Name of the model to perform the tagging.
    """
    self.llm_tagger_type = tagger_type
    self.model_name = model_name

  @functools.cached_property
  def model(self) -> google_genai.GenerativeModel:
    """Initializes GenerativeModel."""
    return google_genai.GenerativeModel(model_name=self.model_name)

  @override
  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(),
    retry=tenacity.retry_if_exception_type(json.decoder.JSONDecodeError),
    reraise=True,
  )
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    logging.debug('Tagging video "%s" with GeminiVideoTagger', medium.name)
    with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
      f.write(medium.content)
      try:
        video_file = google_genai.upload_file(f.name)
        video_file = _get_active_file(video_file)
        result = self.model.generate_content(
          [
            video_file,
            '\n\n',
            f'{self.format_prompt(tagging_options)} ',
          ],
          generation_config=google_genai.GenerationConfig(
            response_mime_type='application/json',
            response_schema=self.response_schema,
          ),
        )
        logging.info(
          'usage_metadata for media %s: %s',
          medium.name,
          proto.Message.to_dict(result.usage_metadata),
        )
      except FailedProcessFileApiError as e:
        raise exceptions.FailedTaggingError(
          f'Unable to process media: {medium.name}'
        ) from e
      finally:
        video_file.delete()

      if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION:
        return tagging_result.TaggingResult(
          identifier=medium.name,
          type='video',
          content=tagging_result.Description(
            text=json.loads(result.text).get('text')
          ),
        )
      tags = [
        tagging_result.Tag(name=r.get('name'), score=r.get('score'))
        for r in json.loads(result.text)
      ]
      return tagging_result.TaggingResult(
        identifier=medium.name, type='video', content=tags
      )

  def format_prompt(self, tagging_options: base.TaggingOptions) -> str:
    """Builds correct prompt to send to LLM.

    Prompt contains format instructions to get output result.

    Args:
      tagging_options: Parameters to refine the prompt.

    Returns:
      Formatted prompt.
    """
    base_prompt = video_llm_tagger_promps[self.llm_tagger_type]
    formatting_instructions = (
      ' For each tag provide name and a score from 0 to 1 '
      'where 0 is tag absence and 1 complete tag presence.'
    )
    prompt = base_prompt.format(**dataclasses.asdict(tagging_options))
    if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION:
      return prompt
    return prompt + formatting_instructions

  @property
  def response_schema(
    self,
  ) -> list[tagging_result.Tag] | tagging_result.Description:
    """Generates correct response schema based on type of LLM tagger."""
    return (
      tagging_result.Description
      if self.llm_tagger_type == LLMTaggerTypeEnum.DESCRIPTION
      else list[tagging_result.Tag]
    )


class UnprocessedFileApiError(Exception):
  """Raised when file wasn't processed via File API."""


class FailedProcessFileApiError(Exception):
  """Raised when file wasn't processed via File API."""


@tenacity.retry(
  stop=tenacity.stop_after_attempt(3),
  wait=tenacity.wait_fixed(5),
  retry=tenacity.retry_if_exception(UnprocessedFileApiError),
  reraise=True,
)
def _get_active_file(
  video_file: google_genai.types.File,
) -> google_genai.types.File:
  """Polls status of video file and returns it if status is ACTIVE."""
  video_file = google_genai.get_file(video_file.name)
  if video_file.state.name == 'ACTIVE':
    return video_file
  if video_file.state.name == 'FAILED':
    raise FailedProcessFileApiError
  raise UnprocessedFileApiError
