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
"""Module for defining common interface for taggers."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
from __future__ import annotations

import abc
import dataclasses
import itertools
import logging
import os
from collections.abc import MutableSequence, Sequence
from concurrent import futures

from media_tagging import media, repository, tagging_result


@dataclasses.dataclass
class TaggingOptions:
  """Specifies options to refine media tagging.

  Attributes:
    n_tags: Max number of tags to return.
    tags: Particular tags to find in the media.
  """

  n_tags: int | None = None
  tags: Sequence[str] | None = None

  def __post_init__(self):  # noqa: D105
    if self.tags and not isinstance(self.tags, MutableSequence):
      self.tags = [tag.strip() for tag in self.tags.split(',')]


class BaseTagger(abc.ABC):
  """Interface to inherit all taggers from."""

  @abc.abstractmethod
  def tag(
    self,
    medium: media.Medium,
    tagging_options: TaggingOptions = TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    """Sends media bytes to tagging engine.

    Args:
      medium: Medium to tag.
      tagging_options: Parameters to refine the tagging results.
      **kwargs: Optional keywords arguments to be sent for tagging.

    Returns:
      Results of tagging.
    """

  def _limit_number_of_tags(
    self, tags: Sequence[tagging_result.Tag], n_tags: int
  ) -> list[tagging_result.Tag]:
    """Returns limited number of tags from the pool.

    Args:
      tags: All tags produced by tagging algorithm.
      n_tags: Max number of tags to return.

    Returns:
      Limited number of tags sorted by the score.
    """
    sorted_tags = sorted(tags, key=lambda x: x.score, reverse=True)
    return sorted_tags[:n_tags]

  def tag_media_sequentially(
    self,
    media_paths: Sequence[str | os.PathLike[str]],
    tagging_parameters: dict[str, str] | None = None,
    persist_repository: repository.Basetagging_result.TaggingResultsRepository
    | None = None,
  ) -> list[tagging_result.TaggingResult]:
    """Runs media tagging algorithm.

    Args:
      media_paths: Local or remote path to media file.
      tagging_parameters: Optional keywords arguments to be sent for tagging.
      persist_repository: Repository to store tagging results.

    Returns:
      Results of tagging for all media.
    """
    if not tagging_parameters:
      tagging_parameters = {}
    results = []
    for path in media_paths:
      medium = media.Medium(path)
      if persist_repository and (
        tagging_results := persist_repository.get([medium.name])
      ):
        logging.info('Getting media from repository: %s', path)
        results.extend(tagging_results)
        continue
      logging.info('Processing media: %s', path)
      tagging_results = self.tag(
        medium,
        tagging_options=TaggingOptions(**tagging_parameters),
      )
      if tagging_results is None:
        continue
      if persist_repository:
        persist_repository.add([tagging_results])
      results.append(tagging_results)
    return results

  def tag_media(
    self,
    media_paths: Sequence[str | os.PathLike[str]],
    tagging_parameters: dict[str, str] | None = None,
    parallel_threshold: int = 1,
    persist_repository: repository.BaseTaggingResultsRepository | None = None,
  ) -> list[tagging_result.TaggingResult]:
    """Runs media tagging algorithm.

    Args:
      media_paths: Local or remote path to media file.
      tagging_parameters: Optional keywords arguments to be sent for tagging.
      parallel_threshold: Number of threads.
      persist_repository: Repository to store tagging results.

    Returns:
      Results of tagging for all media.
    """
    untagged_media = media_paths
    tagged_media = []
    if persist_repository and (
      tagged_media := persist_repository.get(media_paths)
    ):
      tagged_media_names = {media.identifier for media in tagged_media}
      untagged_media = {
        media_path
        for media_path in media_paths
        if media.convert_path_to_media_name(media_path)
        not in tagged_media_names
      }

    if not parallel_threshold:
      return (
        self.tag_media_sequentially(
          untagged_media, tagging_parameters, persist_repository
        )
        + tagged_media
      )
    with futures.ThreadPoolExecutor(max_workers=parallel_threshold) as executor:
      future_to_media_path = {
        executor.submit(
          self.tag_media_sequentially,
          [media_path],
          tagging_parameters,
          persist_repository,
        ): media_path
        for media_path in media_paths
      }
      untagged_media = itertools.chain.from_iterable(
        [
          future.result()
          for future in futures.as_completed(future_to_media_path)
        ]
      )
      return list(untagged_media) + tagged_media
