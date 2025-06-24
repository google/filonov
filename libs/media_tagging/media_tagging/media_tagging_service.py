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

"""Responsible for performing media tagging."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import inspect
import itertools
import logging
import os
from collections.abc import Sequence
from concurrent import futures
from importlib.metadata import entry_points
from typing import Literal

import pydantic

from media_tagging import exceptions, media, repositories, tagging_result
from media_tagging.taggers import TAGGERS
from media_tagging.taggers import base as base_tagger

logger = logging.getLogger('media-tagger')


class MediaTaggingRequest(pydantic.BaseModel):
  """Contains parameters to perform media tagging.

  Attributes:
    tagger_type: Type of tagger to be used.
    media_type: Type of media to tag.
    media_paths: Paths or URLs where media are located.
    tagging_options: Tagging specific parameters.
    parallel_threshold: Maximum number of parallel tagging operations.
    deduplicate: Whether cached results of tagging should be deduplicated.
    media_type_enum: Converted media type.
    tagger: Initialized tagger.
  """

  model_config = pydantic.ConfigDict(extra='ignore')

  tagger_type: str
  media_type: Literal['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO']
  media_paths: set[str] | Sequence[os.PathLike[str] | str]
  tagging_options: base_tagger.TaggingOptions = base_tagger.TaggingOptions()
  parallel_threshold: int = 10
  deduplicate: bool = False

  def model_post_init(self, __context):
    if isinstance(self.media_paths, str):
      self.media_paths = [path.strip() for path in self.media_paths.split(',')]

  @property
  def media_type_enum(self):
    try:
      return media.MediaTypeEnum[self.media_type.upper()]
    except KeyError as e:
      raise media.InvalidMediaTypeError(self.tagging_request.media_type) from e

  @property
  def tagger(self):
    if builtin_tagger_class := TAGGERS.get(self.tagger_type):
      return builtin_tagger_class(
        **self.tagging_options.dict(),
      )
    plugin_taggers = discover_taggers(TAGGERS.keys())
    if plugin_tagger_class := plugin_taggers.get(self.tagger_type):
      return plugin_tagger_class(
        **self.tagging_options.dict(),
      )
    raise base_tagger.TaggerError(
      f'Unsupported type of tagger {self.tagger_type}. '
      f'Supported taggers: {list(TAGGERS.keys())}'
    )


class MediaFetchingRequest(pydantic.BaseModel):
  """Contains parameters to fetching media tagging results from DB.

  Attributes:
    media_type: Type of media to tag.
    media_paths: Paths or URLs where media are located.
    output: Output of tagging: tag or description.
    tagger_type: Type of tagger to be used.
    deduplicate: Whether fetched tagging results should be deduplicated.
  """

  model_config = pydantic.ConfigDict(extra='ignore')

  media_type: Literal['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO']
  media_paths: Sequence[os.PathLike[str] | str]
  output: Literal['tag', 'description']
  tagger_type: str = 'loader'
  deduplicate: bool = False


class MediaTaggingResponse(pydantic.BaseModel):
  """Contains results of tagging.

  Attributes:
    results: Tagging results.
  """

  results: list[tagging_result.TaggingResult]

  def trim(self, min_score: float) -> None:
    """Removes tags from tagging results with scores below threshold."""
    for result in self.results:
      result.trim_tags(min_score)

  def to_garf_report(self):
    return tagging_result.to_garf_report(self.results)

  def to_pandas(self):
    return tagging_result.to_pandas(self.results)

  def __bool__(self) -> bool:
    return bool(self.results)


def discover_taggers(
  existing_taggers: Sequence[str],
) -> dict[str, base_tagger.BaseTagger]:
  """Loads all taggers exposed as `media_tagger` plugin."""
  taggers = {}
  for media_tagger in entry_points(group='media_tagger'):
    if media_tagger.name in existing_taggers:
      continue
    try:
      tagger_module = media_tagger.load()
      for name, obj in inspect.getmembers(tagger_module):
        if inspect.isclass(obj) and issubclass(obj, base_tagger.BaseTagger):
          taggers[obj.alias] = getattr(tagger_module, name)
    except ModuleNotFoundError:
      continue
  return taggers


class MediaTaggingService:
  """Handles tasks related to media tagging.

  Attributes:
    repo: Repository that contains tagging results.
  """

  def __init__(
    self,
    tagging_results_repository: repositories.BaseTaggingResultsRepository
    | None = None,
  ) -> None:
    """Initializes MediaTaggingService."""
    self.repo = (
      tagging_results_repository
      or repositories.SqlAlchemyTaggingResultsRepository()
    )

  def get_media(
    self,
    fetching_request: MediaFetchingRequest,
  ) -> MediaTaggingResponse:
    results = self.repo.get(
      fetching_request.media_paths,
      fetching_request.media_type,
      fetching_request.tagger_type,
      fetching_request.output,
      fetching_request.deduplicate,
    )
    return MediaTaggingResponse(results=results)

  def tag_media(
    self,
    tagging_request: MediaTaggingRequest,
  ) -> MediaTaggingResponse:
    """Tags media based on requested tagger.

    Args:
      tagging_request: Parameters for tagging.

    Returns:
      Results of tagging.
    """
    return self._process_media('tag', tagging_request)

  def describe_media(
    self,
    tagging_request: MediaTaggingRequest,
  ) -> MediaTaggingResponse:
    """Tags media based on requested tagger.

    Args:
      tagging_request: Parameters for tagging.

    Returns:
      Results of tagging.
    """
    return self._process_media('describe', tagging_request)

  def _process_media(
    self,
    action: Literal['tag', 'describe'],
    tagging_request: MediaTaggingRequest,
    deduplicate: bool = False,
  ) -> MediaTaggingResponse:
    """Gets media information based on tagger and output type.

    Args:
      action: Defines output of tagging: tags or description.
      tagging_request: Parameters for tagging.
      deduplicate: Whether cached tagging results should be deduplicated.

    Returns:
      Results of tagging.

    Raises:
      InvalidMediaTypeError: When incorrect media type is provided.
      TaggerError: When incorrect tagger_type is used.
    """
    concrete_tagger = tagging_request.tagger
    media_type_enum = tagging_request.media_type_enum
    output = 'description' if action == 'describe' else 'tag'
    untagged_media = tagging_request.media_paths
    tagged_media = []
    if self.repo and (
      tagged_media := self.repo.get(
        tagging_request.media_paths,
        tagging_request.media_type,
        tagging_request.tagger_type,
        output,
        deduplicate,
      )
    ):
      logger.info('Reusing %d already tagged media', len(tagged_media))
      tagged_media_names = {
        tagged_medium.identifier for tagged_medium in tagged_media
      }
      untagged_media = set()
      for media_path in tagging_request.media_paths:
        if (
          media.convert_path_to_media_name(
            media_path, tagging_request.media_type
          )
          not in tagged_media_names
        ):
          untagged_media.add(media_path)
    if not untagged_media:
      return MediaTaggingResponse(results=tagged_media)

    logger.info('Processing %d media', len(untagged_media))
    if not tagging_request.parallel_threshold:
      results = (
        self._process_media_sequentially(
          action,
          concrete_tagger,
          tagging_request.media_type_enum,
          untagged_media,
          tagging_request.tagging_options,
        )
        + tagged_media
      )
      return MediaTaggingResponse(results=results)
    with futures.ThreadPoolExecutor(
      max_workers=tagging_request.parallel_threshold
    ) as executor:
      future_to_media_path = {
        executor.submit(
          self._process_media_sequentially,
          action,
          concrete_tagger,
          media_type_enum,
          [media_path],
          tagging_request.tagging_options,
        ): media_path
        for media_path in untagged_media
      }
      tagging_results = itertools.chain.from_iterable(
        [
          future.result()
          for future in futures.as_completed(future_to_media_path)
        ]
      )
      results = list(tagging_results) + tagged_media
      return MediaTaggingResponse(results=results)

  def _process_media_sequentially(
    self,
    action: Literal['tag', 'describe'],
    concrete_tagger: base_tagger.BaseTagger,
    media_type: media.MediaTypeEnum,
    media_paths: Sequence[str | os.PathLike[str]],
    tagging_options: base_tagger.TaggingOptions,
  ) -> list[tagging_result.TaggingResult]:
    """Runs media tagging algorithm.

    Args:
      action: Defines output of tagging: tags or description.
      concrete_tagger: Instantiated tagger.
      media_type: Type of media.
      media_paths: Local or remote path to media file.
      tagging_options: Optional parameters to be sent for tagging.

    Returns:
      Results of tagging for all media.
    """
    results = []
    for path in media_paths:
      medium = media.Medium(path, media_type)
      logger.info('Processing media: %s', path)
      try:
        tagging_results = getattr(concrete_tagger, action)(
          medium,
          tagging_options,
        )
        if tagging_results is None:
          continue
        results.append(tagging_results)
        if self.repo:
          self.repo.add([tagging_results])
      except base_tagger.TaggerError as e:
        logger.error('Tagger error: %s', str(e))
      except pydantic.ValidationError as e:
        logger.error('Failed to parse tagging results: %s', str(e))
      except exceptions.FailedTaggingError as e:
        logger.error('Failed to perform tagging: %s', str(e))
      except Exception as e:
        logger.error('Unknown error occurred: %s', str(e))

    return results
