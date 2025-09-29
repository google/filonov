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

import pathlib

import pydantic
import pytest
from media_tagging.taggers import base


class SampleSchema(pydantic.BaseModel):
  element: str


class TestTaggingOptions:
  def test_tagging_options_custom_prompt_from_string_returns_success(self):
    test_prompt = 'test prompt'
    options = base.TaggingOptions(custom_prompt=test_prompt)

    assert options.custom_prompt == test_prompt

  def test_tagging_options_custom_prompt_from_file_returns_success(
    self, tmp_path
  ):
    test_prompt = 'test prompt'
    prompt_file = tmp_path / 'prompt.txt'

    with open(prompt_file, 'w') as f:
      f.write(test_prompt)

    options = base.TaggingOptions(custom_prompt=prompt_file)

    assert options.custom_prompt == test_prompt

  def test_tagging_options_custom_prompt_from_file_raises_error(self):
    test_prompt = 'test_prompt.txt'
    with pytest.raises(FileNotFoundError):
      base.TaggingOptions(custom_prompt=test_prompt)

  @pytest.mark.parametrize(
    'schema,serialized',
    [
      (SampleSchema, 'SampleSchema'),
      ({'type': 'STRING'}, {'type': 'STRING'}),
      (pathlib.Path(__file__).parent / 'test-schema.json', {'type': 'STRING'}),
    ],
  )
  def test_tagging_options_custom_schema_returns_correct_serializer(
    self, schema, serialized
  ):
    options = base.TaggingOptions(custom_schema=schema)
    assert options.dict().get('custom_schema') == serialized
