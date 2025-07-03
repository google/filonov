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
"""Repository for storing SimilarityPairs."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import abc
import itertools
from collections.abc import MutableSequence, Sequence
from typing import Any, Final, Iterable

import sqlalchemy
from media_tagging.repositories import SqlAlchemyRepository
from sqlalchemy.orm import declarative_base
from typing_extensions import override

from media_similarity import media_pair

DEFAULT_CHUNK_SIZE: Final[int] = 100


def _batched(iterable: Iterable[Any], chunk_size: int):
  iterator = iter(iterable)
  while chunk := tuple(itertools.islice(iterator, chunk_size)):
    yield chunk


class BaseSimilarityPairsRepository(abc.ABC):
  """Interface for defining repositories."""

  def get(
    self, pairs: str | Sequence[str], tagger: str | None = None
  ) -> list[media_pair.SimilarityPair]:
    """Specifies get operations."""
    if isinstance(pairs, MutableSequence):
      pairs = {str(pair) for pair in pairs}
    else:
      pairs = (str(pairs),)
    if len(pairs) > DEFAULT_CHUNK_SIZE:
      results = [
        self._get(batch, tagger)
        for batch in _batched(pairs, DEFAULT_CHUNK_SIZE)
      ]
      return list(itertools.chain.from_iterable(results))
    return self._get(pairs, tagger)

  def add(
    self,
    pairs: media_pair.SimilarityPair | Sequence[media_pair.SimilarityPair],
  ) -> None:
    """Specifies add operations."""
    if not isinstance(pairs, MutableSequence):
      pairs = [pairs]
    self._add(pairs)

  @abc.abstractmethod
  def _get(
    self, pairs: str | Sequence[str], tagger: str | None = None
  ) -> list[media_pair.SimilarityPair]:
    """Specifies get operations."""

  @abc.abstractmethod
  def _add(
    self,
    pairs: media_pair.SimilarityPair | Sequence[media_pair.SimilarityPair],
  ) -> None:
    """Specifies get operations."""

  @abc.abstractmethod
  def list(self) -> list[media_pair.SimilarityPair]:
    """Returns all similarity pairs from the repository."""


class InMemorySimilarityPairsRepository(BaseSimilarityPairsRepository):
  """Uses pickle files for persisting tagging results."""

  def __init__(self) -> None:
    """Initializes InMemorySimilarityPairsRepository."""
    self.results = []

  @override
  def _get(
    self, pairs: str | Sequence[str], tagger: str | None = None
  ) -> list[media_pair.SimilarityPair]:
    return [result for result in self.results if result.key in pairs]

  @override
  def _add(
    self,
    pairs: media_pair.SimilarityPair | Sequence[media_pair.SimilarityPair],
  ) -> None:
    self.results.extend(pairs)

  @override
  def list(self) -> list[media_pair.SimilarityPair]:
    return self.results


Base = declarative_base()


class SimilarityPairs(Base):
  """ORM model for persisting SimilarityPair."""

  __tablename__ = 'similarity_pairs'
  tagger = sqlalchemy.Column(sqlalchemy.String(20), primary_key=True)
  identifier = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  score = sqlalchemy.Column(sqlalchemy.Float)
  similarity_weight = sqlalchemy.Column(sqlalchemy.JSON)
  dissimilarity_weight = sqlalchemy.Column(sqlalchemy.JSON)

  def to_model(self) -> media_pair.SimilarityPair:
    """Converts model to SimilarityPair."""
    return media_pair.SimilarityPair(
      tagger=self.tagger,
      media=tuple(self.identifier.split('|')),
      similarity_score=media_pair.SimilarityScore(
        score=self.score,
        similarity_weight=media_pair.Weight(
          n_tags=self.similarity_weight.get('n_tags'),
          normalized_value=self.similarity_weight.get('normalized_value'),
          unnormalized_value=self.similarity_weight.get('unnormalized_value'),
        ),
        dissimilarity_weight=media_pair.Weight(
          n_tags=self.dissimilarity_weight.get('n_tags'),
          normalized_value=self.dissimilarity_weight.get('normalized_value'),
          unnormalized_value=self.dissimilarity_weight.get(
            'unnormalized_value'
          ),
        ),
      ),
    )


class SqlAlchemySimilarityPairsRepository(
  BaseSimilarityPairsRepository, SqlAlchemyRepository
):
  """Uses SqlAlchemy engine for persisting similarity_pairs."""

  def initialize(self) -> None:
    """Creates all ORM objects."""
    Base.metadata.create_all(self.engine)
    super().initialize()

  @override
  def _get(
    self,
    pairs: str | Sequence[str],
    tagger: str | None = None,
  ) -> list[media_pair.SimilarityPair]:
    with self.session() as session:
      query = session.query(SimilarityPairs).where(
        SimilarityPairs.identifier.in_(pairs),
      )
      if tagger:
        query = query.where(SimilarityPairs.tagger == tagger)

      return [res.to_model() for res in query.all()]

  def get_similar_media(
    self, identifier: str, n_results: int = 10, tagger: str | None = None
  ) -> list[media_pair.SimilarityPair]:
    with self.session() as session:
      query = session.query(SimilarityPairs).where(
        SimilarityPairs.identifier.like(f'%{identifier}%'),
      )
      if tagger:
        query = query.where(SimilarityPairs.tagger == tagger)
      return [
        res.to_model()
        for res in query.order_by(SimilarityPairs.score.desc())
        .limit(n_results)
        .all()
      ]

  @override
  def _add(
    self,
    pairs: media_pair.SimilarityPair | Sequence[media_pair.SimilarityPair],
  ) -> None:
    with self.session() as session:
      for pair in pairs:
        session.add(SimilarityPairs(**pair.to_dict()))
      session.commit()

  def list(self) -> list[media_pair.SimilarityPair]:
    """Returns all tagging results from the repository."""
    with self.session() as session:
      return [res.to_model() for res in session.query(SimilarityPairs).all()]
