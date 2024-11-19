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
"""Represent pairs of media."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import dataclasses
import itertools
import sys
from collections.abc import Sequence
from typing import Generator

from media_tagging import tagging_result

from media_similarity import idf_context


class MediaPair:
  """Represents tagging results combined into a single entity.

  Attributes:
    media_1: Concrete instance of TaggingResult.
    media_2: Concrete instance of TaggingResult.
  """

  def __init__(
    self,
    media_1: tagging_result.TaggingResult,
    media_2: tagging_result.TaggingResult,
  ) -> None:
    """Initializes MediaPair."""
    self.media_1 = media_1
    self.media_2 = media_2

  def calculate_similarity(
    self, idf_context_values: idf_context.IdfContext
  ) -> SimilarityPair:
    """Calculates similarity score between media given the IdfContext.

    Similarity score is calculated as a ratio between two elements:
      1. Sum of scores for common tags between media; minimal score is taken.
      2. Sum of scores for unique tags (presented only in one of media).

    Args:
      idf_context_values: Relative importance of each tag.

    Returns:
      Similarity score between media.
    """
    media = tuple(str(self).split('|'))
    tags_1 = set(self.media_1.content)
    tags_2 = set(self.media_2.content)
    if not (similar_tags := tags_1.intersection(tags_2)):
      return SimilarityPair(media, 0.0)
    if not (dissimilar_tags := tags_1.symmetric_difference(tags_2)):
      return SimilarityPair(media, sys.float_info.max)
    min_score_for_similar_tags = sum(
      min(tag1.score, tag2.score) * idf_context_values.get(tag1.name)
      for tag1, tag2 in zip(
        sorted(similar_tags, key=lambda x: x.name),
        sorted(tags_2.intersection(tags_1), key=lambda x: x.name),
      )
    )
    dissimilarity_score = sum(
      t.score * idf_context_values.get(t.name) for t in dissimilar_tags
    )
    return SimilarityPair(
      media, min_score_for_similar_tags / dissimilarity_score
    )

  def __eq__(self, other: MediaPair) -> bool:
    """Compares two MediaPairs based on their identifiers."""
    return set(self.media_1.identifier, self.media_2.identifier) == set(
      other.media_1.identifier, other.media_2.identifier
    )

  def __hash__(self) -> int:
    """Hashes MediaPair based on their identifiers."""
    return hash(self.media_1.identifier, self.media_2.identifier)

  def __str__(self) -> str:
    """String representation of MediaPair based on its sorted identifiers."""
    return (
      f'{self.media_1.identifier}|{self.media_2.identifier}'
      if self.media_1.identifier < self.media_2.identifier
      else f'{self.media_2.identifier}|{self.media_1.identifier}'
    )

  def __repr__(self) -> str:
    """Simplified representation of MediaPair based on its identifiers."""
    return f'MediaPair({self.media_1.identifier}, {self.media_2.identifier})'


def build_media_pairs(
  tagging_results: Sequence[tagging_result.TaggingResult],
) -> Generator[MediaPair, None, None]:
  """Generates media pairs from tagging results.

  Args:
    tagging_results: Results of tagging to generate media pairs.


  Yields:
    MediaPair with unique media identifiers.
  """
  for media_1, media_2 in itertools.combinations(set(tagging_results), 2):
    if media_1.identifier != media_2.identifier:
      yield MediaPair(media_1, media_2)


@dataclasses.dataclass(frozen=True)
class SimilarityPair:
  """Contains information on similarity between two media."""

  media: tuple[str, str]
  similarity_score: float

  def to_tuple(self) -> tuple[str, str, float]:
    """Converts all data to tuple of values."""
    media_1, media_2 = self.media
    return (media_1, media_2, self.similarity_score)

  def to_dict(self) -> dict[str, str | float]:
    """Converts all data to tuple of values."""
    return {'identifier': self.key, 'score': self.similarity_score}

  @property
  def key(self) -> str:
    """Sorted identifiers."""
    media_1, media_2 = self.media
    return (
      f'{media_1}|{media_2}' if media_1 < media_2 else f'{media_2}|{media_1}'
    )

  def __eq__(self, other: SimilarityPair) -> bool:
    """Compares two SimilarityPairs based on their identifiers and score."""
    return (self.key, self.similarity_score) == (
      other.key,
      other.similarity_score,
    )
