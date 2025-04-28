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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Defines helper functions for media tagging entrypoints."""

import os

import pandas as pd
import pydantic
import smart_open

from media_tagging import exceptions


class InputConfig(pydantic.BaseModel):
  """Parameters for reading media urls from a file.

  Attributes:
    path: Path to a CSV file that contains media urls.
    column_name: Column name in a file that contains media_urls.
    skip_rows: Number of rows to skip in a file.
  """

  model_config = pydantic.ConfigDict(extra='ignore')

  path: os.PathLike[str] | str
  column_name: str | None = None
  skip_rows: int = 0


def get_media_paths_from_file(input_config: InputConfig) -> set[str]:
  """Reads media urls from a file and returns unique ones.

  Args:
    input_config: Config for reading data from a file.

  Returns:
    Unique media urls.

  Raises:
    MediaSimilarityError: When specified column with media_urls is not found.
  """
  data = pd.read_csv(
    smart_open.open(input_config.path), skiprows=input_config.skip_rows
  )
  if len(data.columns) == 1:
    column_name = data.columns[0]
  elif (column_name := input_config.column_name) not in data.columns:
    raise exceptions.MediaTaggingError(f'Column {column_name} not found')
  return set(data[column_name].tolist())
