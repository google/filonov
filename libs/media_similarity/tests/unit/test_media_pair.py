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

from __future__ import annotations

import sys

import pytest
from media_similarity import media_pair
from media_tagging import tagging_result

idf_context = {'tag1': 10, 'tag2': 5, 'tag3': 1, 'tag4': 0.1}


class TestMediaPair:
  def test_init_raises_media_pair_error_on_media_with_different_taggers(self):
    media_1 = tagging_result.TaggingResult(
      identifier='media_1',
      type='image',
      tagger='gemini',
      content=(tagging_result.Tag(name='tag1', score=1.0),),
      hash='1',
    )
    media_2 = tagging_result.TaggingResult(
      identifier='media_2',
      type='image',
      tagger='google-cloud',
      content=(tagging_result.Tag(name='tag1', score=1.0),),
      hash='1',
    )

    with pytest.raises(media_pair.MediaPairError):
      media_pair.MediaPair(media_1, media_2)

  def test_calculate_similarity_returns_correct_score(self, media_1, media_2):
    test_media_pair = media_pair.MediaPair(media_1, media_2)
    similarity_pair = test_media_pair.calculate_similarity(idf_context)
    expected_similarity = round(0.5 * 10 / (1.0 * 5 + 1.0 * 1.0), 2)
    assert (
      round(similarity_pair.similarity_score.score, 2) == expected_similarity
    )

  def test_calculate_similarity_returns_max_float_for_totally_similar_videos(
    self, media_1
  ):
    test_media_pair = media_pair.MediaPair(media_1, media_1)
    similarity_pair = test_media_pair.calculate_similarity(idf_context)
    assert similarity_pair.similarity_score.score == sys.float_info.max

  def test_calculate_similarity_returns_zero_for_totally_dissimilar_videos(
    self, media_1, media_3
  ):
    test_media_pair = media_pair.MediaPair(media_1, media_3)
    similarity_pair = test_media_pair.calculate_similarity(idf_context)
    assert similarity_pair.similarity_score.score == 0.0


def test_build_media_pairs_returns_unique_pairs_only(media_1, media_2, media_3):
  media = [media_1, media_2, media_3, media_3]
  test_media_pairs = list(media_pair.build_media_pairs(media))
  assert len(test_media_pairs) == len(set(media))
