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

import pydantic
from media_tagging import tagging_result

from media_similarity import exceptions, idf_context


class MediaPairError(exceptions.MediaSimilarityError):
  """MediaPair specific exception."""


class MediaPair:
  """Represents tagging results combined into a single entity.

  Attributes:
    tagger: Taggers used to tag the media.
    media_1: Concrete instance of TaggingResult.
    media_2: Concrete instance of TaggingResult.
  """

  def __init__(
    self,
    media_1: tagging_result.TaggingResult,
    media_2: tagging_result.TaggingResult,
  ) -> None:
    """Initializes MediaPair."""
    if media_1.tagger != media_2.tagger:
      raise MediaPairError(
        'Media has different tagged using different taggers.'
        f'media_1: {media_1.tagger}, media_2: {media_2.tagger}'
      )
    self.tagger = media_1.tagger
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
    media = tuple(str(self).split('|', maxsplit=2))
    tags_1 = set(self.media_1.content)
    tags_2 = set(self.media_2.content)
    if not (similar_tags := {tag_1 for tag_1 in tags_1 if tag_1 in tags_2}):
      return SimilarityPair(
        self.tagger, media, similarity_score=SimilarityScore(score=0.0)
      )
    if not (dissimilar_tags := tags_1.symmetric_difference(tags_2)):
      return SimilarityPair(
        self.tagger,
        media,
        similarity_score=SimilarityScore(score=sys.float_info.max),
      )
    min_score_for_similar_tags = 0.0
    unnormalized_min_score_for_similar_tags = 0.0
    for tag1, tag2 in zip(
      sorted(similar_tags, key=lambda x: x.name),
      sorted(
        {tag_2 for tag_2 in tags_2 if tag_2 in tags_1}, key=lambda x: x.name
      ),
    ):
      min_score = min(tag1.score, tag2.score)
      min_score_for_similar_tags += min_score * idf_context_values.get(
        tag1.name
      )
      unnormalized_min_score_for_similar_tags += min_score
    dissimilarity_score = 0.0
    unnormalized_dissimilarity_score = 0.0
    for tag in dissimilar_tags:
      dissimilarity_score += tag.score * idf_context_values.get(tag.name)
      unnormalized_dissimilarity_score += tag.score
    return SimilarityPair(
      self.tagger,
      media,
      similarity_score=SimilarityScore(
        score=min_score_for_similar_tags / dissimilarity_score,
        similarity_weight=Weight(
          n_tags=len(similar_tags),
          normalized_value=min_score_for_similar_tags,
          unnormalized_value=unnormalized_min_score_for_similar_tags,
        ),
        dissimilarity_weight=Weight(
          n_tags=len(dissimilar_tags),
          normalized_value=dissimilarity_score,
          unnormalized_value=unnormalized_dissimilarity_score,
        ),
      ),
    )

  def __eq__(self, other: MediaPair) -> bool:
    """Compares two MediaPairs based on their hashes."""
    return set(self.media_1.hash, self.media_2.hash) == set(
      other.media_1.hash, other.media_2.hash
    )

  def __hash__(self) -> int:
    """Hashes MediaPair based on their hashes."""
    return hash(self.media_1.hash, self.media_2.hash)

  def __str__(self) -> str:
    """String representation of MediaPair based on its sorted hashes."""
    return (
      f'{self.media_1.hash}|{self.media_2.hash}'
      if self.media_1.hash < self.media_2.hash
      else f'{self.media_2.hash}|{self.media_1.hash}'
    )

  def __repr__(self) -> str:
    """Simplified representation of MediaPair based on its identifiers."""
    return (
      f'MediaPair({self.tagger}, '
      f'{self.media_1.identifier}, {self.media_2.identifier})'
    )


def build_media_pairs(
  tagging_results: Sequence[tagging_result.TaggingResult],
) -> Generator[MediaPair, None, None]:
  """Generates media pairs from tagging results.

  Args:
    tagging_results: Results of tagging to generate media pairs.

  Yields:
    MediaPair with unique media hashes.
  """
  for media_1, media_2 in itertools.combinations(set(tagging_results), 2):
    if media_1.hash != media_2.hash:
      yield MediaPair(media_1, media_2)


class Weight(pydantic.BaseModel):
  """Contains information on set of tags in a given media pair.

  Attributes:
    n_tags: Number of tags in a set.
    normalized_value: Sum of tag scores adjusted by IDF values of each tag.
    unnormalized_value: Non-adjusted sum of tag scores.
  """

  n_tags: int | None = None
  normalized_value: float | None = None
  unnormalized_value: float | None = None


class SimilarityScore(pydantic.BaseModel):
  """Contains similarity information on a media pair.

  Attributes:
    score: Similarity divided by dissimilarity of a media pair.
    similarity_weight: Information on similar tags in a pair.
    dissimilarity_weight: Information on dissimilar tags in a pair.
  """

  score: float
  similarity_weight: Weight = Weight()
  dissimilarity_weight: Weight = Weight()


@dataclasses.dataclass(frozen=True)
class SimilarityPair:
  """Contains information on similarity between two media given the tagger."""

  tagger: str
  media: tuple[str, str]
  similarity_score: SimilarityScore

  def to_tuple(self) -> tuple[str, str, float]:
    """Converts all data to tuple of values."""
    media_1, media_2 = self.media
    return (media_1, media_2, self.similarity_score.score)

  def to_dict(self) -> dict[str, str | float, dict[str, float]]:
    """Converts all data to tuple of values."""
    similarity_weight = self.similarity_score.similarity_weight
    dissimilarity_weight = self.similarity_score.dissimilarity_weight
    return {
      'tagger': self.tagger,
      'identifier': self.key,
      'score': self.similarity_score.score,
      'similarity_weight': {
        'n_tags': similarity_weight.n_tags,
        'normalized_value': similarity_weight.normalized_value,
        'unnormalized_value': similarity_weight.unnormalized_value,
      },
      'dissimilarity_weight': {
        'n_tags': dissimilarity_weight.n_tags,
        'normalized_value': dissimilarity_weight.normalized_value,
        'unnormalized_value': dissimilarity_weight.unnormalized_value,
      },
    }

  @property
  def key(self) -> str:
    """Sorted identifiers."""
    media_1, media_2 = self.media
    return (
      f'{media_1}|{media_2}' if media_1 < media_2 else f'{media_2}|{media_1}'
    )

  def __eq__(self, other: SimilarityPair) -> bool:
    """Compares two SimilarityPairs based on their keys and score."""
    return (self.key, self.similarity_score) == (
      other.key,
      other.similarity_score,
    )
