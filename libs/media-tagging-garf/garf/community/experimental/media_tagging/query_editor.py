# Copyright 2026 Google LLC
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
"""Defines Media Tagging API specific query parser."""

import json
import re
from collections import defaultdict

import smart_open
from garf.core import query_editor, query_parser


class MediaTaggingApiQueryError(query_parser.GarfQueryError):
  """Query errors."""


class MediaTaggingApiQuery(query_editor.QuerySpecification):
  """Query to Media Tagging API."""

  def extract_filters(self):
    super().extract_filters()
    filters = defaultdict(dict)
    for field in self.query.filters:
      # key, operator, *value = re.split(
      #   pattern=r'(=|in)', string=field.lower(), maxsplit=3
      # )
      key, operator, *value = field.split(' ', maxsplit=3)
      if len(nested_keys := key.split('.')) > 1:
        key, nested_key = nested_keys
      else:
        nested_key = None
      if nested_key == 'custom_schema':
        if (schema := _destringify(value[0])) in (
          'boolean',
          'integer',
          'number',
          'string',
        ):
          filters[key].update({'custom_schema': {'type': schema}})
        elif schema.endswith('.json'):
          try:
            with smart_open.open(schema, 'r', encoding='utf-8') as f:
              schema_data = json.load(f)
              filters[key].update({'custom_schema': schema_data})
          except FileNotFoundError as e:
            raise MediaTaggingApiQueryError(
              f'Failed to read schema from a file {schema}'
            ) from e
        else:
          try:
            full_schema = ' '.join(value).replace("'", '')
            schema_data = json.loads(full_schema)
            filters[key].update({'custom_schema': schema_data})
          except json.decoder.JSONDecoder as e:
            raise MediaTaggingApiQueryError(f'Invalid schema {schema}') from e
        continue
      if operator.lower() == 'in':
        values = re.findall(r'\((.*?)\)', field)
        if not (values := values[0]):
          raise query_parser.GarfQueryError(
            'No values in IN statement: ' + field
          )
        formatted_value = [_destringify(value) for value in values.split(',')]
      else:
        formatted_value = _destringify(' '.join(value))
      if nested_key:
        filters[key].update({nested_key: formatted_value})
      else:
        filters[key] = formatted_value
    if 'media_type' not in filters:
      raise query_parser.GarfQueryError('Missing required filters:')
    self.query.filters = filters
    return self

  def extract_resource_name(self):
    super().extract_resource_name()
    if (unknown_resource := self.query.resource_name) not in (
      'tag',
      'description',
    ):
      raise query_editor.GarfResourceError(
        f'Unsupported resource: {unknown_resource}'
      )
    return self


def _destringify(field: str) -> str:
  return re.sub(r'^[\'"]|[\'"]$', '', field.strip())
