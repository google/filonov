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
from media_tagging import media, tagging_result
from media_tagging.loaders import file


class TestFileLoader:
  @pytest.fixture
  def loader(self):
    return file.FileLoader()

  def test_load_returns_correct_results(self, loader, tmp_path):
    location = tmp_path / 'tags.csv'
    results = pd.DataFrame(
      data=[
        ['test_media', 'test_tag1', 1.0],
        ['test_media', 'test_tag2', 0.1],
      ],
      columns=['media_url', 'tag', 'score'],
    )

    results.to_csv(location)

    tagging_results = loader.load(
      file_column_input=file.TagFileLoaderInput(
        identifier_name='media_url', tag_name='tag', score_name='score'
      ),
      location=location,
      output='tag',
      media_type=media.MediaTypeEnum.IMAGE,
    )
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
    result = tagging_results[0]

    assert result == expected_result
    assert result.tagging_details == {'loader_type': 'file'}
