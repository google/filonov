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
from collections.abc import MutableSequence, Sequence

from media_tagging import media, tagging_result


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
    if self.n_tags:
      self.n_tags = int(self.n_tags)

  def __bool__(self) -> bool:  # noqa: D105
    return bool(self.n_tags or self.tags)


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
