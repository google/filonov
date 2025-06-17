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


from garf_core import report
from media_tagging import tagging_result


def test_to_garf_report_returns_converted_tags():
  test_tagging_results = [
    tagging_result.TaggingResult(
      identifier='test',
      output='tag',
      tagger='gemini',
      type='image',
      content=[tagging_result.Tag(name='test_tag', score=1.0)],
    )
  ]

  converted_report = tagging_result.to_garf_report(test_tagging_results)

  expected_report = report.GarfReport(
    results=[['test', 'tag', 'gemini', 'image', {'test_tag': 1.0}]],
    column_names=['identifier', 'output', 'tagger', 'type', 'content'],
  )

  assert converted_report == expected_report


def test_to_garf_report_returns_converted_description():
  test_tagging_results = [
    tagging_result.TaggingResult(
      identifier='test',
      output='description',
      tagger='gemini',
      type='image',
      content=tagging_result.Description(text='test_description'),
    )
  ]

  converted_report = tagging_result.to_garf_report(test_tagging_results)

  expected_report = report.GarfReport(
    results=[['test', 'description', 'gemini', 'image', 'test_description']],
    column_names=['identifier', 'output', 'tagger', 'type', 'content'],
  )

  assert converted_report == expected_report


def test_to_garf_report_returns_converted_descriptions():
  test_tagging_results = [
    tagging_result.TaggingResult(
      identifier='test',
      output='description',
      tagger='gemini',
      type='image',
      content=[
        tagging_result.Description(text='test_description_1'),
        tagging_result.Description(text='test_description_2'),
      ],
    )
  ]

  converted_report = tagging_result.to_garf_report(test_tagging_results)

  expected_report = report.GarfReport(
    results=[
      [
        'test',
        'description',
        'gemini',
        'image',
        [
          {'text': 'test_description_1'},
          {'text': 'test_description_2'},
        ],
      ]
    ],
    column_names=['identifier', 'output', 'tagger', 'type', 'content'],
  )

  assert converted_report == expected_report
