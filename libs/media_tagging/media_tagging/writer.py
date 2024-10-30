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
"""Module for defining read operations."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import abc
import csv
import json
import os
from collections.abc import Sequence

from typing_extensions import override

from media_tagging import tagging_result


class BaseWriter(abc.ABC):
  """Interface to inherit all writers from."""

  @abc.abstractmethod
  def write(
    self,
    results: Sequence[tagging_result.TaggingResult],
    single_output_name: str | None = None,
  ) -> None:
    """Writes tagging results.

    Args:
      results: Results of media tagging.
      single_output_name: Parameter for saving results to a single file.
    """


class CsvWriter(BaseWriter):
  """Responsible for saving tagging results to CSV."""

  def __init__(
    self,
    destination_folder: str = os.getcwd(),
    **kwargs: str,
  ) -> None:
    """Initializes CsvWriter.

    Args:
      destination_folder: Folder to store output files.
      kwargs: Optional arguments.
    """
    super().__init__(**kwargs)
    self._destination_folder = destination_folder

  @override
  def write(
    self,
    results: Sequence[tagging_result.TaggingResult],
    single_output_name: str | None = None,
  ) -> None:
    header_written = False
    base_header_columns = ['identifier', 'type']
    if single_output_name:
      destination = f'{single_output_name}.csv'
      mode = 'a'
    else:
      mode = 'w'
    for result in results:
      if not single_output_name:
        destination = f'{result.identifier}.csv'
      with open(os.path.join(self._destination_folder, destination), mode) as f:
        writer = csv.writer(f)
        if isinstance(result.content, Sequence):
          for tag in result.content:
            if not header_written:
              writer.writerow(base_header_columns + ['tags.name', 'tags.score'])
              header_written = True
            writer.writerow(
              (result.identifier, result.type, tag.name, tag.score)
            )
        else:
          if not header_written:
            writer.writerow(base_header_columns + ['description'])
            header_written = True
          writer.writerow((result.identifier, result.type, result.content))


class JsonWriter(BaseWriter):
  """Responsible for saving tagging results to Json."""

  def __init__(
    self, destination_folder: str = os.getcwd(), **kwargs: str
  ) -> None:
    """Initializes JsonWriter based on a destination_folder.

    Args:
      destination_folder: A local folder where JSON files are stored.
      kwargs: Optional arguments.
    """
    super().__init__(**kwargs)
    self._destination_folder = destination_folder

  @override
  def write(
    self,
    results: Sequence[tagging_result.TaggingResult],
    single_output_name: str | None = None,
  ) -> None:
    single_output = []
    if single_output_name:
      destination = f'{single_output_name}.json'
    for result in results:
      output = result.dict()
      if not single_output_name:
        destination = f'{result.identifier}.json'
        with open(
          os.path.join(self._destination_folder, destination), 'w'
        ) as f:
          json.dump(output, f)
      else:
        single_output.append(output)
    if single_output:
      with open(os.path.join(self._destination_folder, destination), 'w') as f:
        json.dump(single_output, f)


def create_writer(
  writer_type: str, writer_parameters: dict[str, str] | None = None
) -> BaseWriter:
  """Factory for creating writer based on provided type.

  Args:
    writer_type: Type of writer.
    writer_parameters: Various parameters to instantiate writer.

  Returns:
    Concrete writer class.
  """
  writers = {'csv': CsvWriter, 'json': JsonWriter}
  if not writer_parameters:
    writer_parameters = {}
  if writer := writers.get(writer_type):
    return writer(**writer_parameters)
  raise ValueError(
    f'Incorrect writer {type} is provided, '
    f'valid options: {list(writers.keys())}'
  )
