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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-module-docstring, missing-class-docstring, missing-function-docstring

import json

import pandas as pd
from media_tagging import writer


class TestJsonWriter:
  def test_write_returns_correct_result(self, tmp_path, fake_tagger):
    result = fake_tagger.tag()
    output = tmp_path / f'{result.identifier}.json'
    json_writer = writer.JsonWriter(destination_folder=tmp_path)
    json_writer.write([result])

    expected_result = {
      'identifier': 'test',
      'type': 'image',
      'content': [
        {
          'name': 'test',
          'score': 0.0,
        }
      ],
    }

    with open(output, 'r', encoding='utf-8') as f:
      data = json.load(f)

    assert data == expected_result

  def test_write_to_single_output_returns_correct_result(
    self, tmp_path, fake_tagger
  ):
    result = fake_tagger.tag(image_name='test')
    result2 = fake_tagger.tag(image_name='test2')
    output = tmp_path / 'single_output'
    json_writer = writer.JsonWriter(destination_folder=tmp_path)
    json_writer.write([result, result2], output)

    expected_result = [
      {
        'identifier': 'test',
        'type': 'image',
        'content': [
          {
            'name': 'test',
            'score': 0.0,
          }
        ],
      },
      {
        'identifier': 'test2',
        'type': 'image',
        'content': [
          {
            'name': 'test',
            'score': 0.0,
          }
        ],
      },
    ]

    with open(f'{output}.json', 'r', encoding='utf-8') as f:
      data = json.load(f)

    assert data == expected_result


class TestCsvWriter:
  def test_write_returns_correct_result(self, tmp_path, fake_tagger):
    result = fake_tagger.tag()
    output = tmp_path / f'{result.identifier}.csv'
    csv_writer = writer.CsvWriter(destination_folder=tmp_path)
    csv_writer.write([result])

    expected_result = pd.DataFrame(
      data=[['test', 'image', 'test', 0.0]],
      columns=('identifier', 'type', 'tags.name', 'tags.score'),
    )

    data = pd.read_csv(output)

    assert data.equals(expected_result)

  def test_write_to_single_output_returns_correct_result(
    self, tmp_path, fake_tagger
  ):
    result = fake_tagger.tag()
    output = tmp_path / 'single_output'
    csv_writer = writer.CsvWriter(destination_folder=tmp_path)
    csv_writer.write([result, result], output)

    expected_result = pd.DataFrame(
      data=[
        ['test', 'image', 'test', 0.0],
        ['test', 'image', 'test', 0.0],
      ],
      columns=('identifier', 'type', 'tags.name', 'tags.score'),
    )

    data = pd.read_csv(f'{output}.csv')

    assert data.equals(expected_result)
