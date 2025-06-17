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

"""Handles creative map generation."""

import logging
from collections.abc import Sequence
from typing import ClassVar, Literal

import media_similarity
import media_tagging
import pydantic
from media_tagging.media_tagging_service import (
  MediaFetchingRequest,
  MediaTaggingRequest,
)

from filonov import creative_map, exceptions
from filonov.inputs import input_service

logger = logging.getLogger('filonov')


class OutputParameters(pydantic.BaseModel):
  """Parameters for saving creative maps data.

  Attributes:
    output_name: Fully qualified name to store the results.
    output_type: Type of output.

  """

  output_name: str = 'creative_map'
  output_type: Literal['console', 'file'] = 'file'


class CreativeMapGenerateRequest(pydantic.BaseModel):
  """Specifies structure of request for returning creative map.

  Attributes:
    source: Source of getting data for creative map.
    media_type: Type of media to get.
    tagger: Type of tagger to use.
    tagger_parameters: Parameters to finetune tagging.
    similarity_parameters: Parameters to similarity matching.
    input_parameters: Parameters to get data from the source of creative map.
    output_parameters: Parameters for saving creative maps data.
    parallel_threshold: Tagging and similarity detecting threshold.
    trim_tags_threshold: Keeps tags only with the score higher than threshold.
  """

  default_tagger_parameters: ClassVar[dict[str, int]] = {'n_tags': 100}

  source: input_service.InputSource
  media_type: Literal['IMAGE', 'YOUTUBE_VIDEO'] = 'IMAGE'
  tagger: Literal['gemini', 'google-cloud', 'langchain', 'loader', None] = None
  tagger_parameters: dict[str, str | int] = default_tagger_parameters
  similarity_parameters: dict[str, float | bool | None] = {
    'normalize': False,
    'custom_threshold': None,
  }
  input_parameters: dict[str, str | Sequence[str]] = {}
  output_parameters: OutputParameters = OutputParameters()
  parallel_threshold: int = 10
  trim_tags_threshold: float | None = None

  def model_post_init(self, __context):  # noqa: D105
    if not self.tagger_parameters or 'n_tags' not in self.tagger_parameters:
      self.tagger_parameters = self.default_tagger_parameters


class FilonovService:
  """Responsible for handling requests for creative map input generation."""

  def __init__(
    self,
    tagging_service: media_tagging.MediaTaggingService,
    similarity_service: media_similarity.MediaSimilarityService,
  ) -> None:
    """Initializes FilonovService."""
    self.tagging_service = tagging_service
    self.similarity_service = similarity_service
    self._input_service = None

  def generate_creative_map(
    self,
    source: input_service.InputSource,
    request: CreativeMapGenerateRequest,
  ) -> creative_map.CreativeMap:
    """Generates creative map data.

    Performs the following steps:

    * Input data fetching.
    * Media tagging.
    * Media similarity matching.

    Args:
      source: Supported source of data.
      request: Request for creative maps generation.

    Returns:
      Generated creative map.
    """
    input_parameters = (
      request.input_parameters.dict()
      if isinstance(request.input_parameters, pydantic.BaseModel)
      else request.input_parameters
    )
    logger.info(
      'Fetching input from source %s with parameters: %s',
      request.media_type,
      request.input_parameters,
    )
    media_info, context = input_service.MediaInputService(
      source
    ).generate_media_info(request.media_type, input_parameters)
    if not media_info:
      raise exceptions.FilonovError(
        f'No performance data found for the context: {context}'
      )
    media_urls = {media.media_path for media in media_info.values()}
    if not request.tagger:
      logger.info('Tagger not specified, getting data from DB')
      tagging_results = self.tagging_service.get_media(
        MediaFetchingRequest(
          media_type=request.media_type,
          media_paths=list(media_urls),
          output='tag',
          deduplicate=True,
        )
      )
      if not tagging_results:
        raise exceptions.FilonovError('Failed to get tagging results from DB')
    else:
      logger.info(
        'Performing tagging with tagger %s and  parameters: %s',
        request.tagger,
        request.tagger_parameters,
      )
      tagging_results = self.tagging_service.tag_media(
        MediaTaggingRequest(
          tagger_type=request.tagger,
          media_type=request.media_type,
          tagging_parameters=request.tagger_parameters,
          media_paths=media_urls,
          parallel_threshold=request.parallel_threshold,
          deduplicate=True,
        )
      )
    if not tagging_results:
      raise exceptions.FilonovError(
        f'Failed to perform media tagging for the context: {context}'
      )

    logger.info(
      'Performing similarity detection with parameters: %s',
      request.similarity_parameters,
    )
    clustering_results = self.similarity_service.cluster_media(
      tagging_results=tagging_results.results,
      parallel_threshold=request.parallel_threshold,
      **request.similarity_parameters,
    )
    logger.info('Generating creative map...')
    if trim_threshold := request.trim_tags_threshold:
      tagging_results.trim(trim_threshold)
    return creative_map.CreativeMap.from_clustering(
      clustering_results, tagging_results.results, media_info, context
    )
