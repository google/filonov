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
from media_similarity import repositories
from media_similarity.media_pair import (
  MediaPair,
  SimilarityPair,
  SimilarityScore,
)
from media_tagging import tagging_result

media_1 = tagging_result.TaggingResult(
  identifier='1',
  tagger='gemini',
  type='image',
  content=(tagging_result.Tag(name='test', score=0.0),),
  hash='1',
)
media_2 = tagging_result.TaggingResult(
  identifier='2',
  tagger='gemini',
  type='image',
  content=(tagging_result.Tag(name='test', score=0.0),),
  hash='2',
)

test_similarity_pair = SimilarityPair(
  tagger='gemini',
  media=('2', '1'),
  similarity_score=SimilarityScore(score=1.0),
)


class TestInMemoreSimilarityPairsRepository:
  @pytest.fixture
  def repository(self):
    return repositories.InMemorySimilarityPairsRepository()

  def test_add_populates_repository(self, repository):
    pairs = [test_similarity_pair]
    repository.add(pairs)

    assert repository.results == pairs

  def test_get_returns_correct_pair(self, repository):
    test_pair = MediaPair(media_1, media_2)
    repository.add([test_similarity_pair])
    [extracted_pair] = repository.get([test_pair])
    assert extracted_pair == test_similarity_pair

  def test_list_returns_correct_pairs(self, repository):
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
    test_pair = MediaPair(media_1, media_2)
    repository.add([test_similarity_pair])
    [extracted_pair] = repository.get([test_pair])
    assert extracted_pair == test_similarity_pair

  def test_list_returns_correct_pairs(self, repository):
    repository.add([test_similarity_pair])
    extracted_pairs = repository.list()
    assert extracted_pairs == [test_similarity_pair]
