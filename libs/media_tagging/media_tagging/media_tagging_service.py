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
import contextlib
import inspect
import itertools
import logging
import os
from collections.abc import Sequence
from concurrent import futures
from importlib.metadata import entry_points
from typing import Literal

import pydantic
from rich import progress

from media_tagging import exceptions, media, repositories, tagging_result
from media_tagging.taggers import base as base_tagger


def _load_taggers():
  """Loads all taggers exposed as `media_tagger` plugin."""
  taggers = {}
  for media_tagger in entry_points(group='media_tagger'):
    try:
      tagger_module = media_tagger.load()
      for name, obj in inspect.getmembers(tagger_module):
        if inspect.isclass(obj) and issubclass(obj, base_tagger.BaseTagger):
          taggers[obj.alias] = getattr(tagger_module, name)
    except ModuleNotFoundError:
      continue
  return taggers


TAGGERS = _load_taggers()


class MediaTaggingService:
  """Handles tasks related to media tagging.

  Attributes:
    repo: Repository that contains tagging results.
  """

  def __init__(
    self,
    tagging_results_repository: repositories.BaseTaggingResultsRepository,
  ) -> None:
    """Initializes MediaTaggingService."""
    self.repo = tagging_results_repository

  def tag_media(
    self,
    tagger_type: str,
    media_type: str,
    media_paths: Sequence[os.PathLike[str] | str],
    tagging_parameters: dict[str, str] | None = None,
    parallel_threshold: int = 10,
  ) -> list[tagging_result.TaggingResult]:
    """Tags media based on requested tagger.

    Args:
      tagger_type: Type of tagger use.
      media_type: Type of media.
      media_paths: Path to media.
      tagging_parameters: Additional parameters to use during tagging.
      parallel_threshold: Number of parallel threads to run.

    Returns:
      Results of tagging.
    """
    return self._process_media(
      'tag',
      tagger_type,
      media_type,
      media_paths,
      tagging_parameters,
      parallel_threshold,
    )

  def describe_media(
    self,
    tagger_type: str,
    media_type: str,
    media_paths: Sequence[os.PathLike[str] | str],
    tagging_parameters: dict[str, str] | None = None,
    parallel_threshold: int = 10,
  ) -> list[tagging_result.TaggingResult]:
    """Describes media based on requested tagger.

    Args:
      tagger_type: Type of tagger use.
      media_type: Type of media.
      media_paths: Path to media.
      tagging_parameters: Additional parameters to use during tagging.
      parallel_threshold: Number of parallel threads to run.

    Returns:
      Results of tagging.
    """
    return self._process_media(
      'describe',
      tagger_type,
      media_type,
      media_paths,
      tagging_parameters,
      parallel_threshold,
    )

  def _process_media(
    self,
    action: Literal['tag', 'describe'],
    tagger_type: str,
    media_type: str,
    media_paths: Sequence[os.PathLike[str] | str],
    tagging_parameters: dict[str, str] | None = None,
    parallel_threshold: int = 10,
  ) -> list[tagging_result.TaggingResult]:
    """Gets media information based on tagger and output type.

    Args:
      action: Defines output of tagging: tags or description.
      tagger_type: Type of tagger use.
      media_type: Type of media.
      media_paths: Path to media.
      tagging_parameters: Additional parameters to use during tagging.
      parallel_threshold: Number of parallel threads to run.

    Returns:
      Results of tagging.

    Raises:
      InvalidMediaTypeError: When incorrect media type is provided.
      TaggerError: When incorrect tagger_type is used.
    """
    try:
      media_type_enum = media.MediaTypeEnum[media_type.upper()]
    except KeyError as e:
      raise media.InvalidMediaTypeError(media_type) from e
    if not (tagger_class := TAGGERS.get(tagger_type)):
      raise base_tagger.TaggerError(
        f'Unsupported type of tagger {tagger_type}. '
        f'Supported taggers: {list(TAGGERS.keys())}'
      )
    if not tagging_parameters:
      tagging_parameters = {}
    concrete_tagger = tagger_class(
      **tagging_parameters,
    )
    output = 'description' if action == 'describe' else 'tag'
    untagged_media = media_paths
    tagged_media = []
    if self.repo and (
      tagged_media := self.repo.get(
        media_paths, media_type, tagger_type, output
      )
    ):
      tagged_media_names = {media.identifier for media in tagged_media}
      untagged_media = {
        media_path
        for media_path in media_paths
        if media.convert_path_to_media_name(media_path, media_type)
        not in tagged_media_names
      }
    if not untagged_media:
      return tagged_media

    if not parallel_threshold:
      return (
        self._process_media_sequentially(
          action,
          concrete_tagger,
          media_type_enum,
          untagged_media,
          tagging_parameters,
        )
        + tagged_media
      )
    with futures.ThreadPoolExecutor(max_workers=parallel_threshold) as executor:
      future_to_media_path = {
        executor.submit(
          self._process_media_sequentially,
          action,
          concrete_tagger,
          media_type_enum,
          [media_path],
          tagging_parameters,
        ): media_path
        for media_path in media_paths
      }
      untagged_media = itertools.chain.from_iterable(
        [
          future.result()
          for future in progress.track(
            futures.as_completed(future_to_media_path),
            f'Tagging {len(untagged_media)} media...',
          )
        ]
      )
      return list(untagged_media) + tagged_media

  def _process_media_sequentially(
    self,
    action: Literal['tag', 'describe'],
    concrete_tagger: base_tagger.BaseTagger,
    media_type: media.MediaTypeEnum,
    media_paths: Sequence[str | os.PathLike[str]],
    tagging_parameters: dict[str, str] | None = None,
  ) -> list[tagging_result.TaggingResult]:
    """Runs media tagging algorithm.

    Args:
      action: Defines output of tagging: tags or description.
      concrete_tagger: Instantiated tagger.
      media_type: Type of media.
      media_paths: Local or remote path to media file.
      tagging_parameters: Optional keywords arguments to be sent for tagging.

    Returns:
      Results of tagging for all media.
    """
    if not tagging_parameters:
      tagging_parameters = {}
    results = []
    output = 'description' if action == 'describe' else 'tag'
    tagger_type = concrete_tagger.alias
    for path in media_paths:
      medium = media.Medium(path, media_type)
      if self.repo and (
        tagging_results := self.repo.get(
          [medium.name], media_type, tagger_type, output
        )
      ):
        logging.debug('Getting media from repository: %s', path)
        results.extend(tagging_results)
        continue
      logging.debug('Processing media: %s', path)
      with contextlib.suppress(
        exceptions.FailedTaggingError, pydantic.ValidationError
      ):
        tagging_results = getattr(concrete_tagger, action)(
          medium,
          tagging_options=base_tagger.TaggingOptions.from_dict(
            tagging_parameters
          ),
        )
        if tagging_results is None:
          continue
        results.append(tagging_results)
        if self.repo:
          self.repo.add([tagging_results])
    return results
