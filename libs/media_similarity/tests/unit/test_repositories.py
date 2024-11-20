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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring

import pytest
from media_similarity import media_pair, repositories
from media_tagging import tagging_result

media_1 = tagging_result.TaggingResult(
  identifier='1',
  type='image',
  content=(tagging_result.Tag(name='test', score=0.0),),
)
media_2 = tagging_result.TaggingResult(
  identifier='2',
  type='image',
  content=(tagging_result.Tag(name='test', score=0.0),),
)


class TestInMemoreSimilarityPairsRepository:
  @pytest.fixture
  def repository(self):
    return repositories.InMemorySimilarityPairsRepository()

  def test_add_populates_repository(self, repository):
    pairs = [media_pair.SimilarityPair(media=('1', '2'), similarity_score=1.0)]
    repository.add(pairs)

    assert repository.results == pairs

  def test_get_returns_correct_pair(self, repository):
    test_pair = media_pair.MediaPair(media_1, media_2)
    test_similarity_pair = media_pair.SimilarityPair(
      media=('2', '1'), similarity_score=1.0
    )
    repository.add([test_similarity_pair])
    [extracted_pair] = repository.get([test_pair])
    assert extracted_pair == test_similarity_pair

  def test_list_returns_correct_pairs(self, repository):
    test_similarity_pair = media_pair.SimilarityPair(
      media=('2', '1'), similarity_score=1.0
    )
    repository.add([test_similarity_pair])
    extracted_pairs = repository.list()
    assert extracted_pairs == [test_similarity_pair]


class TestSqlAlchemySimilarityPairsRepository:
  @pytest.fixture()
  def repository(self, tmp_path):
    repo = repositories.SqlAlchemySimilarityPairsRepository(
      db_url=f'sqlite:///{str(tmp_path)}.db'
    )
    repo.initialize()
    return repo

  def test_get_returns_correct_pair(self, repository):
    test_pair = media_pair.MediaPair(media_1, media_2)
    test_similarity_pair = media_pair.SimilarityPair(
      media=('2', '1'), similarity_score=1.0
    )
    repository.add([test_similarity_pair])
    [extracted_pair] = repository.get([test_pair])
    assert extracted_pair == test_similarity_pair

  def test_list_returns_correct_pairs(self, repository):
    test_similarity_pair = media_pair.SimilarityPair(
      media=('2', '1'), similarity_score=1.0
    )
    repository.add([test_similarity_pair])
    extracted_pairs = repository.list()
    assert extracted_pairs == [test_similarity_pair]
