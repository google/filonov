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
import operator
from collections.abc import Sequence
from typing import Any, ClassVar, Literal

import media_fetching
import media_similarity
import media_tagging
import pydantic
from garf.core import GarfReport
from garf.io import writer as garf_writer
from media_tagging import media
from media_tagging.media_tagging_service import (
  MediaFetchingRequest,
  MediaTaggingRequest,
)

from filonov import creative_map, exceptions
from filonov.telemetry import tracer

logger = logging.getLogger('filonov')


class SimilarityParameters(pydantic.BaseModel):
  normalize: bool = False
  custom_threshold: float | None = None
  algorithm: str | None = None


class OutputParameters(pydantic.BaseModel):
  """Parameters for saving creative maps data.

  Attributes:
    output_name: Fully qualified name to store the results.
    output: Type of output.
  """

  output_name: str = 'creative_map'
  output: Literal['map', 'dashboard'] = 'map'


class BaseRequest(pydantic.BaseModel):
  """Specifies structure of request for working with Filonov.

  Attributes:
    source: Source for getting data.
    media_type: Type of media to get from source.
    tagger: Type of tagger to use.
    tagger_parameters: Parameters to finetune tagging.
    similarity_parameters: Parameters to similarity matching.
    source_parameters: Parameters to get data from the source.
    parallel_threshold: Tagging and similarity detecting threshold.
    trim_tags_threshold: Keeps tags only with the score higher than threshold.
  """

  default_tagger_parameters: ClassVar[dict[str, int]] = {'n_tags': 100}

  source: media_fetching.sources.models.InputSource
  media_type: Literal[tuple(media.MediaTypeEnum.options())] | None = None
  tagger: Literal['gemini', 'google-cloud', 'loader', None] = None
  tagger_parameters: dict[str, str | int] | None = None
  similarity_parameters: SimilarityParameters = SimilarityParameters()
  source_parameters: dict[str, bool | int | str | Sequence[str]] = (
    pydantic.Field(default_factory=dict)
  )
  parallel_threshold: int = 10
  trim_tags_threshold: float | None = None
  context: dict[str, Any] = pydantic.Field(default_factory=dict)

  def model_post_init(self, __context):  # noqa: D105
    if not self.tagger_parameters:
      self.tagger_parameters = self.default_tagger_parameters
    if 'n_tags' not in self.tagger_parameters:
      self.tagger_parameters.update(self.default_tagger_parameters)
    if self.source == 'youtube':
      self.media_type = 'YOUTUBE_VIDEO'
      self.tagger = 'gemini'

    source_parameters_class = media_fetching.INPUT_MAPPING.get(self.source)
    if not isinstance(self.source_parameters, source_parameters_class):
      self.source_parameters = source_parameters_class(
        **self.source_parameters, media_type=self.media_type
      )

    self.context.update({self.source: self.source_parameters.model_dump()})


class GenerateTablesRequest(BaseRequest):
  writer: str
  writer_parameters: dict[str, str | int | float | bool] = pydantic.Field(
    default_factory=dict
  )
  output_parameters: OutputParameters = OutputParameters(
    output='dashboard', output_name='filonov'
  )


class GenerateCreativeMapRequest(BaseRequest):
  """Specifies structure of request for returning creative map.

  Attributes:
    source: Source of getting data for creative map.
    media_type: Type of media to get.
    tagger: Type of tagger to use.
    tagger_parameters: Parameters to finetune tagging.
    similarity_parameters: Parameters to similarity matching.
    source_parameters: Parameters to get data from the source of creative map.
    embed_previews: Whether media previews should be embedded into a map.
    context: Overall context of map generation.
  """

  output_parameters: OutputParameters = OutputParameters(
    output='map', output_name='creative_map'
  )
  embed_previews: bool = False
  omit_series: bool = False
  output_type: Literal['file', 'console'] = 'file'


class FilonovService:
  """Responsible for handling requests for creative map input generation."""

  def __init__(
    self,
    fetching_service: media_fetching.MediaFetchingService | None = None,
    tagging_service: media_tagging.MediaTaggingService | None = None,
    similarity_service: media_similarity.MediaSimilarityService | None = None,
  ) -> None:
    """Initializes FilonovService."""
    self.fetching_service = fetching_service
    self.tagging_service = tagging_service
    self.similarity_service = similarity_service

  def _prepare_data_sources(self, request) -> tuple[str]:
    if not request.tagger and not self.tagging_service:
      raise exceptions.FilonovError(
        'Failed to get tagging results from DB. MediaTaggingService missing.'
      )
    if not (fetching_service := self.fetching_service):
      fetching_service = media_fetching.MediaFetchingService.from_source_alias(
        source=request.source
      )
    media_data = fetching_service.fetch(
      request.source_parameters, request.context
    )
    if not media_data:
      raise exceptions.FilonovError(
        'No performance data found for the context.'
      )
    media_urls = media_data['media_url'].to_list(
      row_type='scalar', distinct=True
    )
    if not (tagging_service := self.tagging_service):
      tagging_service = media_tagging.MediaTaggingService()
    if not request.tagger:
      logger.info('Tagger not specified, getting data from DB')
      tagging_response = tagging_service.get_media(
        MediaFetchingRequest(
          media_type=request.media_type,
          media_paths=list(media_urls),
          output='tag',
          deduplicate=True,
        )
      )
      if not tagging_response:
        raise exceptions.FilonovError('No tagging data found in DB.')
    else:
      tagging_response = tagging_service.tag_media(
        MediaTaggingRequest(
          tagger_type=request.tagger,
          media_type=request.media_type,
          tagging_options=request.tagger_parameters,
          media_paths=media_urls,
          parallel_threshold=request.parallel_threshold,
          deduplicate=True,
        ),
        path_processor=request.tagger_parameters.get('path_processor'),
      )
    if not tagging_response:
      raise exceptions.FilonovError(
        'Failed to perform media tagging for the context: '
        f'{request.source_parameters}'
      )
    if not (similarity_service := self.similarity_service):
      similarity_service = (
        media_similarity.MediaSimilarityService.from_connection_string(
          tagging_service.repo.db_url
        )
      )
    clustering_request = media_similarity.MediaClusteringRequest(
      media_type=request.media_type,
      tagger_type=request.tagger,
      tagging_options=GenerateCreativeMapRequest.default_tagger_parameters,
      normalize=request.similarity_parameters.normalize,
      custom_threshold=request.similarity_parameters.custom_threshold,
      algorithm=request.similarity_parameters.algorithm,
      parallel_threshold=request.parallel_threshold,
      tagging_response=tagging_response,
    )
    clustering_results = similarity_service.cluster_media(clustering_request)
    if request.tagger and request.tagger_parameters:
      logger.info('Generating custom tags...')
      tagging_response = tagging_service.tag_media(
        MediaTaggingRequest(
          tagger_type=request.tagger,
          media_type=request.media_type,
          tagging_options=request.tagger_parameters,
          media_paths=media_urls,
          parallel_threshold=request.parallel_threshold,
          deduplicate=True,
        ),
        path_processor=request.tagger_parameters.get('path_processor'),
      )
    if trim_threshold := request.trim_tags_threshold:
      tagging_response.trim(trim_threshold)
    return media_data, tagging_response, clustering_results

  @tracer.start_as_current_span('generate_tables')
  def generate_tables(
    self,
    request: GenerateTablesRequest,
  ) -> None:
    """Generates dashboard data.

    Performs the following steps:

    * Input data fetching.
    * Media tagging.
    * Media similarity matching.

    Args:
      request: Request for creative maps generation.

    Returns:
      Generated creative map.

    Raises:
      FilonovError: When performance or tagging data not found.
    """
    media_data, tagging_response, clustering_results = (
      self._prepare_data_sources(request)
    )
    clusters = clustering_results.clusters
    media_to_tags = {}
    for m in tagging_response.results:
      media_to_tags[m.identifier] = m.content
    media_info = creative_map.convert_report_to_media_info(
      performance=media_data,
      media_type=request.media_type,
      metric_columns=request.source_parameters.metrics,
      segment_columns=request.source_parameters.segments,
      modules=request.source_parameters.extra_info,
    )
    media_url_to_id = {p.media_path: k for k, p in media_info.items()}
    tag_performance = []
    getter = operator.attrgetter(
      *media_data.column_names, 'cluster', 'output_name'
    )
    output_name = request.output_parameters.output_name
    logger.info('Generating dashboard sources...')
    for row in media_data:
      media_id = media_url_to_id.get(row.media_url)
      row['cluster'] = clusters.get(media_id)
      row['output_name'] = output_name
      if tags := media_to_tags.get(media_id):
        for tag in tags:
          tag_performance.append([tag.name, tag.score, *getter(row)])
    tags_report = GarfReport(
      results=tag_performance,
      column_names=['tag', 'score', *media_data.column_names],
    )
    dashboard_writer = garf_writer.create_writer(
      request.writer, **request.writer_parameters
    )
    dashboard_writer.write(media_data, 'media_performance')
    dashboard_writer.write(tags_report, 'tag_performance')

  @tracer.start_as_current_span('generate_creative_map')
  def generate_creative_map(
    self,
    request: GenerateCreativeMapRequest,
  ) -> creative_map.CreativeMap:
    """Generates creative map data.

    Performs the following steps:

    * Input data fetching.
    * Media tagging.
    * Media similarity matching.

    Args:
      request: Request for creative maps generation.

    Returns:
      Generated creative map.

    Raises:
      FilonovError: When performance or tagging data not found.
    """
    media_data, tagging_response, clustering_results = (
      self._prepare_data_sources(request)
    )
    media_info = creative_map.convert_report_to_media_info(
      performance=media_data,
      media_type=request.media_type,
      metric_columns=request.source_parameters.metrics,
      segment_columns=request.source_parameters.segments,
      modules=request.source_parameters.extra_info,
      omit_time_series=request.omit_series,
    )
    logger.info('Generating creative map...')
    return creative_map.CreativeMap.from_clustering(
      clustering_results=clustering_results,
      tagging_results=tagging_response.results,
      extra_info=media_info,
      fetching_request=request.source_parameters.model_dump(),
      embed_previews=request.embed_previews,
    )
