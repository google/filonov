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

"""Utils module for filonov entrypoints."""

from collections.abc import Sequence

import filonov


def build_creative_map_destination(path: str):
  """Build correct output path."""
  if path_elements := path.split('.')[0:-1]:
    path = '.'.join(path_elements)
  return f'{path}.json'


def build_cli_command(
  request: filonov.GenerateCreativeMapRequest, db: str | None
) -> str:
  command_template = (
    'filonov --source {source} \\\n'
    '\t--media-type {media_type} \\\n'
    '\t--tagger {tagger} \\\n'
    '{source_parameters} \\\n'
    '\t--output-name {output}'
  )
  source = request.source.value
  source_parameters = []
  for name, value in request.source_parameters.model_dump().items():
    if not value or name == 'media_type':
      continue
    if isinstance(value, str):
      source_parameters.append(f'\t--{source}.{name}={value}')
    elif isinstance(value, Sequence):
      value_concat = ','.join(value)
      source_parameters.append(f'\t--{source}.{name}={value_concat}')

  source_parameters = ' \\\n'.join(source_parameters)
  params = {
    'source': source,
    'media_type': request.media_type,
    'tagger': request.tagger,
    'output': request.output_parameters.output_name,
    'source_parameters': source_parameters,
  }
  non_db_command = command_template.format(**params).strip()
  if db:
    return f'{non_db_command} \\\n\t--db-uri {db}'
  return non_db_command
