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
import functools
import itertools
import operator

from media_similarity import adaptive_threshold, media_pair

similarity_pairs = {
  media_pair.SimilarityPair(('media_1', 'media_2'), 10),
  media_pair.SimilarityPair(('media_2', 'media_3'), 10),
  media_pair.SimilarityPair(('media_1', 'media_3'), 10),
  media_pair.SimilarityPair(('media_1', 'media_4'), 10),
  media_pair.SimilarityPair(('media_2', 'media_4'), 10),
  media_pair.SimilarityPair(('media_3', 'media_4'), 10),
}


def test_compute_adaptive_threshold_returns_correct_result():
  computed_threshold = adaptive_threshold.compute_adaptive_threshold(
    similarity_pairs, normalize=True
  )
  assert computed_threshold == adaptive_threshold.AdaptiveThreshold(
    1.85, len(similarity_pairs)
  )


def test_compute_adaptive_threshold_returns_correct_result_with_slices():
  thresholds = []
  thresholds.append(
    adaptive_threshold.compute_adaptive_threshold(
      itertools.islice(similarity_pairs, 1)
    )
  )
  thresholds.append(
    adaptive_threshold.compute_adaptive_threshold(
      itertools.islice(similarity_pairs, 1, 6)
    )
  )
  computed_threshold = functools.reduce(operator.add, thresholds)
  assert computed_threshold == adaptive_threshold.AdaptiveThreshold(
    0.0, len(similarity_pairs)
  )
  computed_threshold.normalize()
  assert computed_threshold == adaptive_threshold.AdaptiveThreshold(
    adaptive_threshold.MINIMAL_ADAPTIVE_THRESHOLD, len(similarity_pairs)
  )
