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
from typing import Final

import pydantic
import tenacity
from google import genai
from typing_extensions import override

from media_tagging import media, tagging_result
from media_tagging.taggers import base
from media_tagging.taggers.llm import utils

MAX_NUMBER_LLM_TAGS: Final[int] = 10


logging.getLogger('google_genai.models').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)


class GeminiModelParameters(pydantic.BaseModel):
  temperature: float | None = None
  top_p: float | None = None
  top_k: int | None = None
  max_output_token: int | None = None

  def dict(self) -> dict[str, float | int]:
    return {k: v for k, v in self.model_dump().items() if v}


class GeminiTaggingStrategy(base.TaggingStrategy):
  """Defines set of operations specific to tagging natively via Gemini."""

  def __init__(
    self,
    model_name: str,
    model_parameters: GeminiModelParameters,
  ) -> None:
    """Initializes GeminiTaggingStrategy.

    Args:
      model_name: Name of the model to perform the tagging.
      model_parameters: Various parameters to finetune the model.
    """
    self.model_name = model_name
    self.model_parameters = model_parameters
    self._client = None
    self._prompt = ''
    self._response_schema = None

  @functools.cached_property
  def client(self) -> genai.Client:
    """Initializes GenerativeModel."""
    if not self._client:
      self._client = genai.Client()
    return self._client

  def get_response_schema(self, output):
    """Generates correct response schema based on type of output."""
    if self._response_schema:
      return self._response_schema
    if output == tagging_result.Description:
      response_schema = output
    else:
      response_schema = list[output]
    self._response_schema = response_schema
    return self._response_schema

  def build_content(self, medium: media.Medium, **kwargs: str):
    """Specifies how media content is converted to Part."""
    raise NotImplementedError

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
    output: tagging_result.TaggingOutput,
    tagging_options: base.TaggingOptions = base.TaggingOptions(),
  ):
    """Sends request to Gemini for tagging medium.

    Args:
      medium: Instantiated media object.
      output: Type of output to request from Gemini.
      tagging_options: Additional parameters to fine-tune tagging.

    Returns:
      Formatted response from Gemini.
    """
    logging.debug('Tagging %s "%s"', medium.type, medium.name)
    prompt = self.build_prompt(medium.type, output, tagging_options)
    media_content = self.build_content(medium, **tagging_options.model_dump())
    prompt_config = genai.types.GenerateContentConfig(
      response_mime_type='application/json',
    )
    if not tagging_options.no_schema:
      prompt_config.response_schema = self.get_response_schema(output)
    response = self.client.models.generate_content(
      model=self.model_name,
      contents=[
        media_content,
        prompt,
      ],
      config=prompt_config,
    )
    if hasattr(response, 'usage_metadata'):
      logging.debug(
        'usage_metadata for media %s: %s',
        medium.name,
        response.usage_metadata.dict(),
      )
    return response

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
    prompt = utils.read_prompt_content(prompt_file_name)
    parameters = utils.get_invocation_parameters(
      media_type=media_type.name,
      tagging_options=tagging_options,
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
      tagging_options.n_tags = MAX_NUMBER_LLM_TAGS
    result = self.get_llm_response(medium, tagging_result.Tag, tagging_options)
    tags = json.loads(result.text)
    if not tagging_options.no_schema:
      tags = [
        tagging_result.Tag(name=r.get('name'), score=r.get('score'))
        for r in tags
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

    description = json.loads(result.text)
    if not tagging_options.no_schema:
      description = description.get('text')
    return tagging_result.TaggingResult(
      identifier=medium.name,
      type=medium.type.name.lower(),
      content=tagging_result.Description(text=description),
    )


class ImageTaggingStrategy(GeminiTaggingStrategy):
  """Defines Gemini specific tagging strategy for images."""

  def build_content(self, medium, **kwargs):
    return genai.types.Part.from_bytes(
      data=medium.content, mime_type='image/jpeg'
    )


class VideoTaggingStrategy(GeminiTaggingStrategy):
  """Defines handling of LLM interaction for video files."""

  def build_content(self, medium, **kwargs):
    return genai.types.Part(
      inline_data=genai.types.Blob(data=medium.content, mime_type='video/mp4'),
      video_metadata=_get_video_metadata(**kwargs),
    )


class YouTubeVideoTaggingStrategy(GeminiTaggingStrategy):
  """Defines handling of LLM interaction for YouTube links."""

  def build_content(self, medium, **kwargs):
    if not medium.content:
      return genai.types.Part(
        file_data=genai.types.FileData(file_uri=medium.media_path),
        video_metadata=_get_video_metadata(**kwargs),
      )
    return genai.types.Part(
      inline_data=genai.types.Blob(data=medium.content, mime_type='video/mp4'),
      video_metadata=_get_video_metadata(**kwargs),
    )


def _get_video_metadata(**kwargs: str) -> genai.types.VideoMetadata:
  d = {
    k: v
    for k, v in kwargs.items()
    if k in genai.types.VideoMetadata.model_fields
  }
  return genai.types.VideoMetadata(**d)
