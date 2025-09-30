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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from media_similarity import adaptive_threshold
from media_similarity.media_pair import SimilarityPair, SimilarityScore

similarity_pairs = [
  SimilarityPair(
    tagger='gemini',
    media=('media_1', 'media_2'),
    similarity_score=SimilarityScore(score=0),
  ),
  SimilarityPair(
    tagger='gemini',
    media=('media_2', 'media_3'),
    similarity_score=SimilarityScore(score=1),
  ),
  SimilarityPair(
    tagger='gemini',
    media=('media_1', 'media_3'),
    similarity_score=SimilarityScore(score=3),
  ),
  SimilarityPair(
    tagger='gemini',
    media=('media_1', 'media_4'),
    similarity_score=SimilarityScore(score=10),
  ),
  SimilarityPair(
    tagger='gemini',
    media=('media_2', 'media_4'),
    similarity_score=SimilarityScore(score=10),
  ),
  SimilarityPair(
    tagger='gemini',
    media=('media_3', 'media_4'),
    similarity_score=SimilarityScore(score=10),
  ),
]


def test_compute_adaptive_threshold_returns_correct_result():
  computed_threshold = adaptive_threshold.compute_adaptive_threshold(
    similarity_pairs, normalize=True
  )
  assert computed_threshold == adaptive_threshold.AdaptiveThreshold(
    14.51, len(similarity_pairs)
  )
