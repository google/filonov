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
import pytest
from garf.community.experimental.media_tagging.query_editor import (
  MediaTaggingApiQuery,
)
from garf.core import query_editor, query_parser


class TestMediaTaggingApiQuery:
  def test_generate_raises_error_on_unsupported_resource(self):
    with pytest.raises(query_editor.GarfResourceError):
      MediaTaggingApiQuery(
        text='SELECT media_url FROM unknown_resource'
      ).generate()

  def test_generate_raises_error_on_missing_media_type(self):
    with pytest.raises(query_parser.GarfQueryError):
      MediaTaggingApiQuery(
        text='SELECT media_url FROM tag WHERE tagger_type = gemini'
      ).generate()

  def test_generate_processes_filters(self):
    query = """
        SELECT
          media_url
        FROM tag
        WHERE
          tagger_type = gemini
          AND media_type = IMAGE
          AND media_path IN (example.com, example2.com)
          AND tagging_options.custom_prompt = "Do something"
          AND tagging_options.model_name = 'gemini-3.0-flash'
      """
    query_elements = MediaTaggingApiQuery(text=query).generate()
    expected_filters = {
      'tagger_type': 'gemini',
      'media_type': 'IMAGE',
      'media_path': ['example.com', 'example2.com'],
      'tagging_options': {
        'custom_prompt': 'Do something',
        'model_name': 'gemini-3.0-flash',
      },
    }
    assert query_elements.filters == expected_filters
