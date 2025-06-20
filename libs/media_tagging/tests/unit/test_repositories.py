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

import pytest
from media_tagging import repositories, tagging_result


class TestSqlAlchemyTaggingResultsRepository:
  @pytest.fixture
  def repo(self):
    return repositories.SqlAlchemyTaggingResultsRepository()

  def test_get_dedup_tags(self, repo):
    tagging_result_1 = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='tag',
      content=[tagging_result.Tag(name='tag1', score=0.1)],
      tagging_details={'tags': 'tag1'},
    )
    tagging_result_2 = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='tag',
      content=[tagging_result.Tag(name='tag2', score=0.1)],
      tagging_details={'n_tags': 1},
    )
    tagging_result_3 = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='tag',
      content=[tagging_result.Tag(name='tag2', score=0.1)],
      tagging_details={'n_tags': 1},
    )

    repo.add(tagging_result_1)
    repo.add(tagging_result_2)
    repo.add(tagging_result_3)

    tagging_results = repo.get(
      media_paths='test1',
      media_type='image',
      tagger_type='gemini',
      output='tag',
      deduplicate=True,
    )

    expected_tagging_results = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='tag',
      content=[
        tagging_result.Tag(name='tag1', score=0.1),
        tagging_result.Tag(name='tag2', score=0.1),
      ],
    )

    assert len(tagging_results) == 1
    assert expected_tagging_results == tagging_results[0]

  def test_get_dedup_descriptions(self, repo):
    tagging_result_1 = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='description',
      content=tagging_result.Description(text='test1'),
    )
    tagging_result_2 = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='description',
      content=tagging_result.Description(text='test2'),
    )
    tagging_result_3 = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='description',
      content=tagging_result.Description(text='test2'),
    )

    repo.add(tagging_result_1)
    repo.add(tagging_result_2)
    repo.add(tagging_result_3)

    tagging_results = repo.get(
      media_paths='test1',
      media_type='image',
      tagger_type='gemini',
      output='describe',
      deduplicate=True,
    )

    expected_tagging_results = tagging_result.TaggingResult(
      identifier='test1',
      type='image',
      tagger='gemini',
      output='description',
      content={
        tagging_result.Description(text='test1'),
        tagging_result.Description(text='test2'),
      },
    )

    assert len(tagging_results) == 1
    assert expected_tagging_results == tagging_results[0]
