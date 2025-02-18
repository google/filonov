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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Defined tagging strategies specific to Gemini."""

import functools
import json
import logging
import tempfile

import google.generativeai as google_genai
import langchain_google_genai as genai
import proto
import tenacity
from google.api_core import exceptions as google_api_exceptions
from langchain_core import output_parsers
from typing_extensions import override
from vertexai import generative_models as google_generative_models

from media_tagging import exceptions, media, tagging_result
from media_tagging.taggers import base
from media_tagging.taggers.llm import langchain_tagging_strategies, utils


class ImageTaggingStrategy(langchain_tagging_strategies.ImageTaggingStrategy):
  """Defines Gemini specific tagging strategy for images."""

  @override
  def __init__(
    self,
    model_name: str,
  ) -> None:
    super().__init__(llm=genai.ChatGoogleGenerativeAI(model=model_name))


class GeminiTaggingStrategy(base.TaggingStrategy):
  """Defines set of operations specific to tagging natively via Gemini."""

  def __init__(
    self,
    model_name: str,
  ) -> None:
    """Initializes GeminiTaggingStrategy.

    Args:
      model_name: Name of the model to perform the tagging.
    """
    self.model_name = model_name
    self._model = None
    self._prompt = ''

  def get_llm_response(
    self,
    medium: media.Medium,
    output: type[tagging_result.TaggingOutput],
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    """Defines how to interact with Gemini to perform media tagging.

    Args:
      medium: Instantiated media object.
      output: Type of output to request from Gemini.
      tagging_options: Additional parameters to fine-tune tagging.
    """
    raise NotImplementedError

  def build_prompt(
    self,
    media_type: media.MediaTypeEnum,
    output: tagging_result.TaggingOutput,
    tagging_options: base.TaggingOptions,
  ) -> str:
    """Builds correct prompt to send to Gemini."""
    if self._prompt:
      return self._prompt
    if custom_prompt := tagging_options.custom_prompt:
      self._prompt = custom_prompt
      return self._prompt
    prompt_file_name = 'tag' if output == tagging_result.Tag else 'description'
    format_instructions = output_parsers.JsonOutputParser(
      pydantic_object=output
    ).get_format_instructions()
    prompt = utils.read_prompt_content(prompt_file_name)
    parameters = utils.get_invocation_parameters(
      media_type=media_type.name,
      tagging_options=tagging_options,
      format_instructions=format_instructions,
    )
    self._prompt = prompt.format(**parameters)
    return self._prompt

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    if not tagging_options:
      tagging_options = base.TaggingOptions(
        n_tags=langchain_tagging_strategies.MAX_NUMBER_LLM_TAGS
      )
    result = self.get_llm_response(medium, tagging_result.Tag, tagging_options)
    tags = [
      tagging_result.Tag(name=r.get('name'), score=r.get('score'))
      for r in json.loads(result.text)
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
    result = self.get_llm_response(
      medium, tagging_result.Description, tagging_options
    )
    description = json.loads(result.text).get('text')
    return tagging_result.TaggingResult(
      identifier=medium.name,
      type=medium.type.name.lower(),
      content=tagging_result.Description(text=description),
    )


class VideoTaggingStrategy(GeminiTaggingStrategy):
  """Defines handling of LLM interaction for video files."""

  @functools.cached_property
  def model(self) -> google_genai.GenerativeModel:
    """Initializes GenerativeModel."""
    if not self._model:
      self._model = google_genai.GenerativeModel(model_name=self.model_name)
    return self._model

  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(),
    retry=tenacity.retry_if_exception_type(json.decoder.JSONDecodeError),
    reraise=True,
  )
  def get_llm_response(
    self,
    medium: media.Medium,
    output: tagging_result.TaggingOutput,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    """Sends request to Gemini for tagging video file.

    Args:
      medium: Instantiated media object.
      output: Type of output to request from Gemini.
      tagging_options: Additional parameters to fine-tune tagging.

    Returns:
      Formatted response from Gemini.

    Raises:
      FailedTaggingError: When video wasn't successfully uploaded.
    """
    logging.debug('Tagging video "%s"', medium.name)
    with tempfile.NamedTemporaryFile(suffix='.mp4') as f:
      f.write(medium.content)
      try:
        video_file = google_genai.upload_file(f.name)
        video_file = _get_active_file(video_file)
        prompt = self.build_prompt(medium.type, output, tagging_options)
        response = self.model.generate_content(
          [
            video_file,
            '\n\n',
            prompt,
          ],
          generation_config=google_genai.GenerationConfig(
            response_mime_type='application/json',
            response_schema=output,
          ),
        )
        if hasattr(response, 'usage_metadata'):
          logging.debug(
            'usage_metadata for media %s: %s',
            medium.name,
            proto.Message.to_dict(response.usage_metadata),
          )
        return response
      except FailedProcessFileApiError as e:
        raise exceptions.FailedTaggingError(
          f'Unable to process media: {medium.name}'
        ) from e
      finally:
        video_file.delete()


class YouTubeVideoTaggingStrategy(GeminiTaggingStrategy):
  """Defines handling of LLM interaction for YouTube links."""

  def __init__(self, model_name: str) -> None:
    """Initializes YouTubeVideoTaggingStrategy."""
    super().__init__(model_name)
    self._response_schema = None

  @functools.cached_property
  def model(self) -> google_genai.GenerativeModel:
    """Initializes GenerativeModel."""
    if not self._model:
      self._model = google_generative_models.GenerativeModel(
        model_name=self.model_name
      )
    return self._model

  def get_response_schema(self, output):
    """Generates correct response schema based on type of output."""
    if self._response_schema:
      return self._response_schema
    if output == tagging_result.Description:
      response_schema = {
        'type': 'object',
        'properties': {'text': {'type': 'string'}},
      }
    else:
      tag_descriptions = tagging_result.Tag.field_descriptions()
      response_schema = {
        'type': 'array',
        'items': {
          'type': 'object',
          'properties': {
            'name': {
              'type': 'STRING',
              'description': tag_descriptions.get('name'),
            },
            'score': {
              'type': 'NUMBER',
              'description': tag_descriptions.get('score'),
            },
          },
        },
      }
    self._response_schema = response_schema
    return self._response_schema

  @override
  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(),
    retry=tenacity.retry_if_exception_type(json.decoder.JSONDecodeError),
    reraise=True,
  )
  def get_llm_response(
    self,
    medium: media.Medium,
    output: type[tagging_result.TaggingOutput],
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    logging.debug('Tagging video "%s"', medium.name)
    video_file = google_generative_models.Part.from_uri(
      uri=medium.media_path, mime_type='video/*'
    )
    try:
      prompt = self.build_prompt(medium.type, output, tagging_options)
      return self.model.generate_content(
        [
          video_file,
          '\n\n',
          prompt,
        ],
        generation_config=google_generative_models.GenerationConfig(
          response_mime_type='application/json',
          response_schema=self.get_response_schema(output),
        ),
      )
    except google_api_exceptions.PermissionDenied as e:
      logging.error('Cannot access video %s', medium.media_path)
      raise exceptions.FailedTaggingError(
        f'Unable to process media: {medium.name}'
        'Reason: Cannot access YouTube video',
      ) from e
    except Exception as e:
      logging.error('Failed to get response from Gemini: %s', e)
      raise exceptions.FailedTaggingError(
        f'Unable to process media: {medium.name}, Reason: {str(e)}',
      ) from e


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
