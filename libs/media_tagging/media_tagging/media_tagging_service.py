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
import itertools
import logging
import os
from collections.abc import Sequence
from concurrent import futures

from media_tagging import media, repositories, tagger, tagging_result
from media_tagging.taggers import base as base_tagger


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
    media_paths: Sequence[os.PathLike[str] | str],
    tagging_parameters: dict[str, str] | None = None,
    parallel_threshold: int = 10,
  ) -> list[tagging_result.TaggingResult]:
    """Tags media using via requested tagger_type.

    Args:
      tagger_type: Type of tagger use.
      media_paths: Path to media.
      tagging_parameters: Additional parameters to use during tagging.
      parallel_threshold: Number of parallel threads to run.

    Returns:
      Results of tagging.
    """
    concrete_tagger = tagger.create_tagger(tagger_type)
    untagged_media = media_paths
    tagged_media = []
    if self.repo and (tagged_media := self.repo.get(media_paths)):
      tagged_media_names = {media.identifier for media in tagged_media}
      untagged_media = {
        media_path
        for media_path in media_paths
        if media.convert_path_to_media_name(media_path)
        not in tagged_media_names
      }
    if not untagged_media:
      return tagged_media

    if not parallel_threshold:
      return (
        self._tag_media_sequentially(
          concrete_tagger, untagged_media, tagging_parameters
        )
        + tagged_media
      )
    with futures.ThreadPoolExecutor(max_workers=parallel_threshold) as executor:
      future_to_media_path = {
        executor.submit(
          self._tag_media_sequentially,
          concrete_tagger,
          [media_path],
          tagging_parameters,
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

  def _tag_media_sequentially(
    self,
    concrete_tagger: base_tagger.BaseTagger,
    media_paths: Sequence[str | os.PathLike[str]],
    tagging_parameters: dict[str, str] | None = None,
  ) -> list[tagging_result.TaggingResult]:
    """Runs media tagging algorithm.

    Args:
      concrete_tagger: Instantiated tagger.
      media_paths: Local or remote path to media file.
      tagging_parameters: Optional keywords arguments to be sent for tagging.

    Returns:
      Results of tagging for all media.
    """
    if not tagging_parameters:
      tagging_parameters = {}
    results = []
    for path in media_paths:
      medium = media.Medium(path)
      if self.repo and (tagging_results := self.repo.get([medium.name])):
        logging.info('Getting media from repository: %s', path)
        results.extend(tagging_results)
        continue
      logging.info('Processing media: %s', path)
      tagging_results = concrete_tagger.tag(
        medium,
        tagging_options=base_tagger.TaggingOptions(**tagging_parameters),
      )
      if tagging_results is None:
        continue
      results.append(tagging_results)
      if self.repo:
        self.repo.add([tagging_results])
    return results
