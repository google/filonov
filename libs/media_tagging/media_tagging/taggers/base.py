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
from typing import Literal

import pydantic
import tenacity

from media_tagging import media, tagging_result


@dataclasses.dataclass
class TaggingOptions:
  """Specifies options to refine media tagging.

  Attributes:
    n_tags: Max number of tags to return.
    tags: Particular tags to find in the media.
    custom_prompt: User provided prompt.
  """

  n_tags: int | None = None
  tags: Sequence[str] | None = None
  custom_prompt: str | None = None

  def __post_init__(self):  # noqa: D105
    if self.tags and not isinstance(self.tags, MutableSequence):
      self.tags = [tag.strip() for tag in self.tags.split(',')]
    if self.n_tags:
      self.n_tags = int(self.n_tags)

  @classmethod
  def from_dict(cls, input_dict: dict[str, int | str | Sequence[str]]):
    """Instantiates TaggingOptions based on an input dict."""
    valid_kwargs = {}
    for key, value in input_dict.items():
      if key in cls.__dataclass_fields__:
        valid_kwargs[key] = value
    return cls(**valid_kwargs)

  def dict(self):
    """Converts TaggingOptions to dict."""
    return dataclasses.asdict(self)

  def __bool__(self) -> bool:  # noqa: D105
    return bool(self.n_tags or self.tags or self.custom_prompt)


class TaggingStrategy(abc.ABC):
  """Interface to inherit all tagging strategies from.

  Tagging strategy should have two methods

  * `tag` - to get structured representation of a media (tags).
  * `describe` - to get unstructured representation (description).
  """

  @abc.abstractmethod
  def tag(
    self,
    medium: media.Medium,
    tagging_options: TaggingOptions = TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    """Tags media based on specified parameters."""

  @abc.abstractmethod
  def describe(
    self,
    medium: media.Medium,
    tagging_options: TaggingOptions = TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    """Describes media based on specified parameters."""

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


class BaseTagger(abc.ABC):
  """Interface to inherit all taggers from.

  BaseTaggger has two main methods:

  * `tag` - to get structured representation of a media (tags).
  * `describe` - to get unstructured representation (description).
  """

  def __init__(self) -> None:
    """Initializes BaseTagger based on type of media and desired output."""
    self._tagging_strategy = None

  @abc.abstractmethod
  def create_tagging_strategy(self, media_type: media.MediaTypeEnum):
    """Creates tagging strategy for the specified media type."""

  def get_tagging_strategy(self, media_type: media.MediaTypeEnum):
    """Strategy for tagging concrete media_type and output."""
    if not self._tagging_strategy:
      self._tagging_strategy = self.create_tagging_strategy(media_type)
    return self._tagging_strategy

  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type(pydantic.ValidationError),
    reraise=True,
  )
  def tag(
    self,
    medium: media.Medium,
    tagging_options: TaggingOptions = TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    """Tags media based on specified parameters."""
    result = self.get_tagging_strategy(medium.type).tag(
      medium, tagging_options, **kwargs
    )
    return self._enrich_tagging_result(
      output='tag', result=result, tagging_options=tagging_options
    )

  @tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    retry=tenacity.retry_if_exception_type(pydantic.ValidationError),
    reraise=True,
  )
  def describe(
    self,
    medium: media.Medium,
    tagging_options: TaggingOptions = TaggingOptions(),
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    """Describes media based on specified parameters."""
    result = self.get_tagging_strategy(medium.type).describe(
      medium, tagging_options, **kwargs
    )
    return self._enrich_tagging_result(
      output='description', result=result, tagging_options=tagging_options
    )

  def _enrich_tagging_result(
    self,
    output: Literal['tag', 'description'],
    result: tagging_result.TaggingResult,
    tagging_options: TaggingOptions,
  ) -> tagging_result.TaggingResult:
    """Adds to tagging result extra parameters."""
    parameters = result.dict()
    if tagging_details := tagging_options.dict():
      tagging_details = {k: v for k, v in tagging_details.items() if v}
    else:
      tagging_details = {}
    parameters.update(
      {
        'tagger': self.alias,
        'output': output,
        'tagging_details': tagging_details,
      }
    )
    return tagging_result.TaggingResult(**parameters)


class TaggerError(Exception):
  """Exception for incorrect taggers."""


class UnsupportedMethodError(TaggerError):
  """Specified unsupported methods for tagging strategies."""


class MediaMismatchError(Exception):
  """Exception for incorrectly selected media for tagger."""
