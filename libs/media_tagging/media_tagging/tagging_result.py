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

from typing import Literal

import pydantic


class Tag(pydantic.BaseModel):
  """Represents a single tag.

  Attributes:
    name: Descriptive name of the tag.
    score: Score assigned to the tag.
  """

  model_config = pydantic.ConfigDict(frozen=True)

  name: str = pydantic.Field(description='tag_name')
  score: float = pydantic.Field(description='tag_score from 0 to 1')

  def __hash__(self) -> int:  # noqa: D105
    return hash(self.name)

  def __eq__(self, other: Tag) -> bool:  # noqa: D105
    return self.name == other.name


class Description(pydantic.BaseModel):
  """Represents brief description of the media.

  Attributes:
    text: Textual description of the media.
  """

  text: str = pydantic.Field(description='brief description of the media')


class TaggingResult(pydantic.BaseModel):
  """Contains tagging information for a given identifier.

  Attributes:
    identifier: Unique identifier of a media being tagged.
    type: Type of media.
    tags: Tags associated with a given media.
  """

  model_config = pydantic.ConfigDict(frozen=True)

  identifier: str = pydantic.Field(description='media identifier')
  type: Literal['image', 'video', 'youtube_video'] = pydantic.Field(
    description='type of media'
  )
  content: tuple[Tag, ...] | Description = pydantic.Field(
    description='tags or description in the result'
  )
