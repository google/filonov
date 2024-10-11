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
"""Specifies AdaptiveThreshold class and compute_adaptive_threshold function.

AdaptiveThreshold is used to identify whether media in a given a media pair
are considered similar based on their similarity score.
"""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import dataclasses
import sys
from typing import Final

import numpy as np

MINIMAL_ADAPTIVE_THRESHOLD: Final[float] = 1.85


@dataclasses.dataclass
class AdaptiveThreshold:
  """Specifies threshold to identify similar media.

  Attributes:
    threshold: Threshold value.
    num_pairs: Number of similarity pairs used to calculate the threshold.
    normalized: Whether the threshold values should be normalized.
  """

  threshold: float
  num_pairs: int
  normalized: bool = False

  def __post_init__(self) -> None:  # noqa: D105
    if self.normalized:
      self.normalize()

  def normalize(self) -> None:
    """Ensures that threshold values is not smaller that minimal one."""
    self.threshold = max(MINIMAL_ADAPTIVE_THRESHOLD, self.threshold)

  def __eq__(self, other: AdaptiveThreshold) -> bool:
    """Compares two thresholds with 2 digit precision."""
    return (round(self.threshold, 2), self.num_pairs) == (
      round(other.threshold, 2),
      other.num_pairs,
    )


def compute_adaptive_threshold(
  similarity_scores: list, normalize: bool = False
) -> AdaptiveThreshold:
  """Calculates threshold based on provided similarity pairs.

  Args:
    similarity_scores: Scores for provided similarity pairs.
    normalize: Whether to perform threshold normalization.

  Returns:
    Calculated adaptive threshold.
  """
  similarity_scores = [
    s.similarity_score
    for s in similarity_scores
    if s.similarity_score < sys.float_info.max
  ]
  threshold_value = np.sqrt(
    np.std(similarity_scores) + np.median(similarity_scores)
  )
  return AdaptiveThreshold(
    threshold=threshold_value,
    num_pairs=len(similarity_scores),
    normalized=normalize,
  )
