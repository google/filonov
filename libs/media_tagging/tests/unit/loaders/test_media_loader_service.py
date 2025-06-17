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
import pandas as pd
import pytest
from media_tagging import media, repositories, tagging_result
from media_tagging.loaders import media_loader_service


class TestMediaLoaderService:
  @pytest.fixture
  def service(self):
    return media_loader_service.MediaLoaderService(
      repositories.SqlAlchemyTaggingResultsRepository()
    )

  def test_load_media_tags_returns_correct_results(self, service, tmp_path):
    location = tmp_path / 'tags.csv'
    results = pd.DataFrame(
      data=[
        ['test_media', 'test_tag1', 1.0],
        ['test_media', 'test_tag2', 0.1],
      ],
      columns=['media_url', 'tag', 'score'],
    )

    results.to_csv(location)
    expected_result = tagging_result.TaggingResult(
      identifier='test_media',
      type=media.MediaTypeEnum.IMAGE.name.lower(),
      tagger='loader',
      content=(
        tagging_result.Tag(name='test_tag1', score=1.0),
        tagging_result.Tag(name='test_tag2', score=0.1),
      ),
      output='tag',
      tagging_details={'loader_type': 'file'},
    )
    service.load_media_tags(
      loader_type='file',
      media_type='IMAGE',
      location=location,
    )
    found_tagging_results = service.repo.get(
      ['test_media'], 'image', 'loader', 'tag'
    )
    assert found_tagging_results[0] == expected_result

  def test_load_media_description_returns_correct_results(
    self, service, tmp_path
  ):
    location = tmp_path / 'descriptions.csv'
    results = pd.DataFrame(
      data=[
        ['test_media', 'test_description'],
      ],
      columns=['media_url', 'text'],
    )

    results.to_csv(location)
    expected_result = tagging_result.TaggingResult(
      identifier='test_media',
      type=media.MediaTypeEnum.IMAGE.name.lower(),
      tagger='loader',
      content=tagging_result.Description(text='test_description'),
      output='description',
      tagging_details={'loader_type': 'file'},
    )
    service.load_media_descriptions(
      loader_type='file',
      media_type='IMAGE',
      location=location,
    )
    found_tagging_results = service.repo.get(
      ['test_media'], 'image', 'loader', 'description'
    )
    assert found_tagging_results[0] == expected_result
