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

from media_similarity import adaptive_threshold, media_pair

similarity_pairs = {
  media_pair.SimilarityPair(('media_1', 'media_2'), 0),
  media_pair.SimilarityPair(('media_2', 'media_3'), 1),
  media_pair.SimilarityPair(('media_1', 'media_3'), 3),
  media_pair.SimilarityPair(('media_1', 'media_4'), 10),
  media_pair.SimilarityPair(('media_2', 'media_4'), 10),
  media_pair.SimilarityPair(('media_3', 'media_4'), 10),
}


def test_compute_adaptive_threshold_returns_correct_result():
  computed_threshold = adaptive_threshold.compute_adaptive_threshold(
    similarity_pairs, normalize=True
  )
  assert computed_threshold == adaptive_threshold.AdaptiveThreshold(
    3.3, len(similarity_pairs)
  )
