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
"""Defines Google Ads API specific query parser."""

import re
from collections import defaultdict

from garf.core import query_editor, query_parser


class MediaTaggingApiQuery(query_editor.QuerySpecification):
  """Query to Media Tagging API."""

  def extract_filters(self):
    super().extract_filters()
    filters = defaultdict(dict)
    for field in self.query.filters:
      key, operator, *value = field.split(' ', maxsplit=3)
      if len(nested_keys := key.split('.')) > 1:
        key, nested_key = nested_keys
      else:
        nested_key = None
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
