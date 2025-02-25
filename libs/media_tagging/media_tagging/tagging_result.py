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
import os
from collections.abc import Sequence
from typing import Any, Literal

import garf_core
import pandas as pd
import pydantic


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

  name: str = pydantic.Field(description='tag_name')
  score: float = pydantic.Field(description='tag_score from 0 to 1')

  def __hash__(self) -> int:  # noqa: D105
    return hash(self.name)

  def __eq__(self, other: Tag) -> bool:  # noqa: D105
    return self.name == other.name


class Description(TaggingOutput):
  """Represents brief description of the media.

  Attributes:
    text: Textual description of the media.
  """

  text: str = pydantic.Field(description='brief description of the media')


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
  content: tuple[Tag, ...] | Description = pydantic.Field(
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

  def __hash__(self):  # noqa: D105
    return hash(
      (self.identifier, self.type, self.content, self.tagger, self.output)
    )

  def __eq__(self, other) -> bool:  # noqa: D105
    return (
      self.identifier,
      self.type,
      self.content,
      self.tagger,
      self.output,
    ) == (
      other.identifier,
      other.type,
      other.content,
      other.tagger,
      other.output,
    )


@dataclasses.dataclass
class TaggingResultsFileInput:
  """Specifies column names in input file."""

  identifier_name: str
  tag_name: str
  score_name: str


def from_file(
  path: os.PathLike[str],
  file_column_input: TaggingResultsFileInput,
  media_type: Literal['image', 'video', 'youtube_video'],
  min_threshold: float = 0.0,
) -> list[TaggingResult]:
  """Build tagging results from a file.

  Args:
    path: Path to files with tags.
    file_column_input: Identifiers for building tagging results.
    media_type: Type of media found in a file.
    min_threshold: Optional threshold for reducing output size.

  Returns:
    File content converted to Tagging results.

  Raises:
    ValueError: If file doesn't have all required input columns.
  """
  identifier, tag, score = (
    file_column_input.identifier_name,
    file_column_input.tag_name,
    file_column_input.score_name,
  )
  data = pd.read_csv(path)
  if missing_columns := {identifier, tag, score}.difference(set(data.columns)):
    raise ValueError(f'Missing column(s) in {path}: {missing_columns}')
  data = data[data[score] > min_threshold]
  data['tag'] = data.apply(
    lambda row: Tag(name=row[tag], score=row[score]),
    axis=1,
  )
  grouped = data.groupby(identifier).tag.apply(list).reset_index()
  return [
    TaggingResult(identifier=row[identifier], type=media_type, content=row.tag)
    for _, row in grouped.iterrows()
  ]


def convert_tagging_results_to_garf_report(
  tagging_results: Sequence[TaggingResult],
) -> garf_core.report.GarfReport:
  """Convert results of tagging to GarfReport for further writing."""
  results = []
  column_names = [
    'identifier',
    'output',
    'tagger',
    'type',
    'tagging_details',
    'content',
  ]
  for result in tagging_results:
    parsed_result = [
      result.identifier,
      result.output,
      result.tagger,
      result.type,
      result.tagging_details,
    ]
    if isinstance(result.content, Description):
      parsed_result.append(result.content.text)
    else:
      parsed_result.append({tag.name: tag.score for tag in result.content})
    results.append(parsed_result)
  return garf_core.report.GarfReport(results=results, column_names=column_names)
