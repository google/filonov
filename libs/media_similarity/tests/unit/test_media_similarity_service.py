# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring

from __future__ import annotations

import pytest
from media_similarity import (
  adaptive_threshold,
  exceptions,
  media_pair,
  media_similarity_service,
  repositories,
)


class TestMediaSimilarityService:
  @pytest.fixture(scope='class')
  def repo(self):
    return repositories.SqlAlchemySimilarityPairsRepository()

  @pytest.fixture
  def service(self, repo):
    return media_similarity_service.MediaSimilarityService(repo)

  def test_cluster_media_raises_similarity_error_when_no_tagging_results(
    self, service
  ):
    with pytest.raises(
      exceptions.MediaSimilarityError, match='No tagging results found.'
    ):
      service.cluster_media(tagging_results=[])

  def test_cluster_media_returns_correct_clusters(
    self, service, media_1, media_2, media_3
  ):
    clustering_results = service.cluster_media([media_1, media_2, media_3])
    calculated_clusters = clustering_results.clusters

    assert (
      calculated_clusters['media_1']
      != calculated_clusters['media_2']
      != calculated_clusters['media_3']
    )

  def test_find_similar_media_returns_correct_results(self, repo, service):
    repo.add(
      [
        media_pair.SimilarityPair('gemini', ('media_1', 'media_2'), 100),
        media_pair.SimilarityPair('gemini', ('media_1', 'media_3'), 10),
        media_pair.SimilarityPair('gemini', ('media_1', 'media_4'), 1),
      ]
    )
    result = service.find_similar_media('media_1', n_results=1)
    expected_result = media_similarity_service.SimilaritySearchResults(
      seed_media_identifier='media_1', results={'media_2': 100.0}
    )

    assert result == [expected_result]


def test_calculate_cluster_assisnment():
  similarity_pairs = {
    media_pair.SimilarityPair('gemini', ('media_1', 'media_2'), 10),
    media_pair.SimilarityPair('gemini', ('media_2', 'media_3'), 10),
    media_pair.SimilarityPair('gemini', ('media_1', 'media_3'), 10),
    media_pair.SimilarityPair('gemini', ('media_1', 'media_4'), 10),
    media_pair.SimilarityPair('gemini', ('media_2', 'media_4'), 10),
    media_pair.SimilarityPair('gemini', ('media_3', 'media_4'), 10),
  }

  calculated_clusters = media_similarity_service._calculate_cluster_assignments(
    similarity_pairs, adaptive_threshold.AdaptiveThreshold(5, 6)
  )
  expected_clusters = {
    'media_1': 1,
    'media_2': 1,
    'media_3': 1,
    'media_4': 1,
  }

  assert calculated_clusters.clusters == expected_clusters
