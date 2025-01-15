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
from sqlalchemy.ext.declarative import declarative_base
from typing_extensions import override

from media_similarity import media_pair

DEFAULT_CHUNK_SIZE: Final[int] = 100


def _batched(iterable: Iterable[Any], chunk_size: int):
  iterator = iter(iterable)
  while chunk := tuple(itertools.islice(iterator, chunk_size)):
    yield chunk


class BaseSimilarityPairsRepository(abc.ABC):
  """Interface for defining repositories."""

  def get(self, pairs: str | Sequence[str]) -> list[media_pair.SimilarityPair]:
    """Specifies get operations."""
    if isinstance(pairs, MutableSequence):
      pairs = {str(pair) for pair in pairs}
    else:
      pairs = (str(pairs),)
    if len(pairs) > DEFAULT_CHUNK_SIZE:
      results = [
        self._get(batch) for batch in _batched(pairs, DEFAULT_CHUNK_SIZE)
      ]
      return list(itertools.chain.from_iterable(results))
    return self._get(pairs)

  def add(
    self,
    pairs: media_pair.SimilarityPair | Sequence[media_pair.SimilarityPair],
  ) -> None:
    """Specifies add operations."""
    if not isinstance(pairs, MutableSequence):
      pairs = [pairs]
    self._add(pairs)

  @abc.abstractmethod
  def _get(self, pairs: str | Sequence[str]) -> list[media_pair.SimilarityPair]:
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
  def _get(self, pairs: str | Sequence[str]) -> list[media_pair.SimilarityPair]:
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
  identifier = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  score = sqlalchemy.Column(sqlalchemy.Float)

  def to_model(self) -> media_pair.SimilarityPair:
    """Converts model to SimilarityPair."""
    return media_pair.SimilarityPair(
      media=tuple(self.identifier.split('|')),
      similarity_score=self.score,
    )


class SqlAlchemySimilarityPairsRepository(BaseSimilarityPairsRepository):
  """Uses SqlAlchemy engine for persisting similarity_pairs."""

  def __init__(self, db_url: str) -> None:
    """Initializes SqlAlchemySimilarityPairsRepository."""
    self.db_url = db_url

  def initialize(self) -> None:
    """Creates all ORM objects."""
    Base.metadata.create_all(self.engine)

  @property
  def session(self) -> sqlalchemy.orm.Session:
    """Property for initializing session."""
    return sqlalchemy.orm.sessionmaker(bind=self.engine)

  @property
  def engine(self) -> sqlalchemy.engine.Engine:
    """Initialized SQLalchemy engine."""
    return sqlalchemy.create_engine(self.db_url)

  @override
  def _get(self, pairs: str | Sequence[str]) -> list[media_pair.SimilarityPair]:
    with self.session() as session:
      return [
        res.to_model()
        for res in session.query(SimilarityPairs)
        .where(SimilarityPairs.identifier.in_(pairs))
        .all()
      ]

  def get_similar_media(
    self, identifier: str, n_results: int = 10
  ) -> list[media_pair.SimilarityPair]:
    with self.session() as session:
      return [
        res.to_model()
        for res in session.query(SimilarityPairs)
        .where(SimilarityPairs.identifier.like(f'%{identifier}%'))
        .order_by(SimilarityPairs.score.desc())
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
