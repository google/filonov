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
from __future__ import annotations

from media_similarity import (
  adaptive_threshold,
  media_pair,
  media_similarity_service,
)


def test_cluster_media_returns_currect_clusters(media_1, media_2, media_3):
  clustering_results = media_similarity_service.cluster_media(
    [media_1, media_2, media_3]
  )
  calculated_clusters = clustering_results.clusters

  assert (
    calculated_clusters['media_1']
    != calculated_clusters['media_2']
    != calculated_clusters['media_3']
  )


def test_calculate_cluster_assisnment():
  similarity_pairs = {
    media_pair.SimilarityPair(('media_1', 'media_2'), 10),
    media_pair.SimilarityPair(('media_2', 'media_3'), 10),
    media_pair.SimilarityPair(('media_1', 'media_3'), 10),
    media_pair.SimilarityPair(('media_1', 'media_4'), 10),
    media_pair.SimilarityPair(('media_2', 'media_4'), 10),
    media_pair.SimilarityPair(('media_3', 'media_4'), 10),
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
