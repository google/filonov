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

import media_tagging
import pytest
from media_similarity import (
  adaptive_threshold,
  exceptions,
  media_similarity_service,
  repositories,
)
from media_similarity.media_pair import SimilarityPair, SimilarityScore


class TestMediaSimilarityService:
  @pytest.fixture
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
      request = media_similarity_service.MediaClusteringRequest(
        media_type='TEXT',
        media_paths=['test'],
        tagger_type=None,
      )
      service.cluster_media(request)

  def test_cluster_media_returns_correct_clusters(
    self, service, media_1, media_2, media_3
  ):
    tagging_response = media_tagging.media_tagging_service.MediaTaggingResponse(
      results=[media_1, media_2, media_3]
    )
    request = media_similarity_service.MediaClusteringRequest(
      media_type='TEXT',
      tagging_response=tagging_response,
    )
    clustering_results = service.cluster_media(request)
    calculated_clusters = clustering_results.clusters

    assert (
      calculated_clusters['media_1']
      != calculated_clusters['media_2']
      != calculated_clusters['media_3']
    )

  def test_find_similar_media_returns_correct_results(self, repo, service):
    repo.add(
      [
        SimilarityPair(
          'gemini', ('media_1', 'media_2'), SimilarityScore(score=100)
        ),
        SimilarityPair(
          'gemini', ('media_1', 'media_3'), SimilarityScore(score=10)
        ),
        SimilarityPair(
          'gemini', ('media_1', 'media_4'), SimilarityScore(score=1)
        ),
      ]
    )
    request = media_similarity_service.MediaSimilaritySearchRequest(
      media_type='TEXT',
      media_paths=['media_1'],
      n_results=1,
    )
    result = service.find_similar_media(request)
    expected_result = media_similarity_service.SimilaritySearchResults(
      seed_media_identifier='media_1', results={'media_2': 100.0}
    )

    assert result == [expected_result]


def test_calculate_cluster_assisnment():
  similarity_pairs = [
    SimilarityPair('gemini', ('1', '2'), SimilarityScore(score=10)),
    SimilarityPair('gemini', ('2', '3'), SimilarityScore(score=10)),
    SimilarityPair('gemini', ('1', '3'), SimilarityScore(score=10)),
    SimilarityPair('gemini', ('1', '4'), SimilarityScore(score=10)),
    SimilarityPair('gemini', ('2', '4'), SimilarityScore(score=10)),
    SimilarityPair('gemini', ('3', '4'), SimilarityScore(score=10)),
  ]

  mapping_table = {str(i): f'media_{i}' for i in range(1, 5)}
  calculated_clusters = media_similarity_service._calculate_cluster_assignments(
    similarity_pairs, adaptive_threshold.AdaptiveThreshold(5, 6), mapping_table
  )
  expected_clusters = {
    'media_1': 1,
    'media_2': 1,
    'media_3': 1,
    'media_4': 1,
  }

  assert calculated_clusters.clusters == expected_clusters
