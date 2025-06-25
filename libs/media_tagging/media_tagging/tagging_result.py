# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License")
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

import dataclasses
import datetime
import json
from collections.abc import Sequence
from typing import Any, Literal

import pandas as pd
import pydantic
from garf_core import report

from media_tagging import exceptions


class TaggingOutput(pydantic.BaseModel):
  """Base class."""

  @classmethod
  def field_descriptions(cls) -> dict[str, str]:
    return {
      name: content.get('description')
      for name, content in json.loads(cls.schema_json())
      .get('properties')
      .items()
    }


class Tag(TaggingOutput):
  """Represents a single tag.

  Attributes:
    name: Descriptive name of the tag.
    score: Score assigned to the tag.
  """

  model_config = pydantic.ConfigDict(frozen=True)

  name: str
  score: float

  def __hash__(self) -> int:  # noqa: D105
    return hash(self.name)

  def __eq__(self, other: Tag) -> bool:  # noqa: D105
    return self.name == other.name


class Description(TaggingOutput):
  """Represents brief description of the media.

  Attributes:
    text: Textual description of the media.
  """

  text: str | list[Any]

  def __hash__(self) -> int:  # noqa: D105
    return hash(self.text)

  def __eq__(self, other: Description) -> bool:  # noqa: D105
    return self.text == other.text


class TaggingResult(pydantic.BaseModel):
  """Contains tagging information for a given identifier.

  Attributes:
    processed_at: Time in UTC timezone when media was processed.
    identifier: Unique identifier of a media being tagged.
    type: Type of media.
    content: Tags / description associated with a given media.
    tagger: Tagger used to generating the content.
    output: Type of tagging output (tag or description).
    tagging_details: Additional details used to perform the tagging.
  """

  processed_at: datetime.datetime = pydantic.Field(
    description='When the media was processed',
    default_factory=datetime.datetime.utcnow,
  )
  identifier: str = pydantic.Field(description='media identifier')
  type: Literal['image', 'video', 'youtube_video'] = pydantic.Field(
    description='type of media'
  )
  content: tuple[Tag, ...] | Description | list[Description] = pydantic.Field(
    description='tags or description in the result'
  )
  tagger: str | None = pydantic.Field(
    description='type of tagger used', default=None
  )
  output: Literal['tag', 'description'] | None = pydantic.Field(
    description='type of output', default=None
  )
  tagging_details: dict[str, Any] | None = pydantic.Field(
    description='Additional details used during tagging', default=None
  )

  def trim_tags(self, value: float) -> None:
    """Removes tags from tagging result with low scores."""
    if isinstance(self.content, Description):
      raise exceptions.MediaTaggingError('Trimming is only supported for tags.')
    self.content = [tag for tag in self.content if tag.score > value]

  def __hash__(self):  # noqa: D105
    return hash(
      (self.identifier, self.type, self.content, self.tagger, self.output)
    )

  def __eq__(self, other) -> bool:  # noqa: D105
    return (
      self.identifier,
      self.type,
      self.output,
      self.tagger,
      self.output,
      self.tagging_details,
    ) == (
      other.identifier,
      other.type,
      other.output,
      other.tagger,
      other.output,
      other.tagging_details,
    )


@dataclasses.dataclass
class TaggingResultsFileInput:
  """Specifies column names in input file."""

  identifier_name: str
  tag_name: str
  score_name: str


def to_garf_report(
  tagging_results: Sequence[TaggingResult],
) -> report.GarfReport:
  """Converts results of tagging to GarfReport for further writing."""
  results = []
  column_names = [
    'identifier',
    'output',
    'tagger',
    'type',
    'content',
  ]
  content_type = None
  content_writer_fns = {
    'description': lambda content: content.text,
    'descriptions': lambda content: [
      {'text': description.text} for description in content
    ],
    'tags': lambda content: {tag.name: tag.score for tag in content},
  }
  for result in tagging_results:
    parsed_result = [
      result.identifier,
      result.output,
      result.tagger,
      result.type,
    ]

    if not content_type:
      if isinstance(result.content, Description):
        content_type = 'description'
      elif isinstance(result.content, Sequence):
        if isinstance(result.content[0], Description):
          content_type = 'descriptions'
        elif isinstance(result.content[0], Tag):
          content_type = 'tags'
    if fn := content_writer_fns.get(content_type):
      parsed_result.append(fn(result.content))
    else:
      parsed_result.append(None)
    results.append(parsed_result)
  return report.GarfReport(results=results, column_names=column_names)


def to_pandas(
  tagging_results: Sequence[TaggingResult],
) -> pd.DataFrame:
  """Converts results of tagging to pandas DataFrame."""
  return to_garf_report(tagging_results).to_pandas()
