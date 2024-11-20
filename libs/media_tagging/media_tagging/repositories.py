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
"""Repository for Tagging results."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import abc
import os
import pickle
from collections.abc import Sequence

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from typing_extensions import override

from media_tagging import media, tagging_result


class BaseTaggingResultsRepository(abc.ABC):
  """Interface for defining repositories."""

  @abc.abstractmethod
  def get(
    self, media_paths: str | Sequence[str]
  ) -> list[tagging_result.TaggingResult]:
    """Specifies get operations."""

  @abc.abstractmethod
  def add(
    self,
    tagging_results: tagging_result.TaggingResult
    | Sequence[tagging_result.TaggingResult],
  ) -> None:
    """Specifies add operations."""

  def list(self) -> list[tagging_result.TaggingResult]:
    """Returns all tagging results from the repository."""
    return self.results


class PickleTaggingResultsRepository(BaseTaggingResultsRepository):
  """Uses pickle files for persisting tagging results."""

  def __init__(
    self, destination: str | os.PathLike[str] = '/tmp/media_tagging.pickle'
  ) -> None:
    """Initializes PickleTaggingResultsRepository."""
    self.destination = destination
    try:
      with open(self.destination, 'rb') as f:
        self.results = pickle.load(f)
    except FileNotFoundError:
      self.results = []

  @override
  def get(
    self, media_paths: Sequence[str]
  ) -> list[tagging_result.TaggingResult]:
    converted_media_paths = [
      media.convert_path_to_media_name(media_path) for media_path in media_paths
    ]
    return [
      result
      for result in self.results
      if result.identifier in converted_media_paths
    ]

  @override
  def add(
    self, tagging_results: Sequence[tagging_result.TaggingResult]
  ) -> None:
    for result in tagging_results:
      self.results.append(result)
    with open(self.destination, 'wb') as f:
      pickle.dump(self.results, f)


class InMemoryTaggingResultsRepository(BaseTaggingResultsRepository):
  """Uses pickle files for persisting tagging results."""

  def __init__(self) -> None:
    """Initializes InMemoryTaggingResultsRepository."""
    self.results = []

  @override
  def get(
    self, media_paths: Sequence[str]
  ) -> list[tagging_result.TaggingResult]:
    converted_media_paths = [
      media.convert_path_to_media_name(media_path) for media_path in media_paths
    ]
    return [
      result
      for result in self.results
      if result.identifier in converted_media_paths
    ]

  @override
  def add(
    self, tagging_results: Sequence[tagging_result.TaggingResult]
  ) -> None:
    for result in tagging_results:
      self.results.append(result)


Base = declarative_base()


class TaggingResults(Base):
  """ORM model for persisting TaggingResult."""

  __tablename__ = 'tagging_results'
  identifier = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  type = sqlalchemy.Column(sqlalchemy.String(10), primary_key=True)
  content = sqlalchemy.Column(sqlalchemy.JSON)

  def to_pydantic_model(self) -> tagging_result.TaggingResult:
    """Converts model to pydantic object."""
    return tagging_result.TaggingResult(
      identifier=self.identifier, type=self.type, content=self.content
    )


class SqlAlchemyTaggingResultsRepository(BaseTaggingResultsRepository):
  """Uses SqlAlchemy engine for persisting tagging results."""

  def __init__(self, db_url: str) -> None:
    """Initializes SqlAlchemyTaggingResultsRepository."""
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

  def get(
    self, media_paths: str | Sequence[str]
  ) -> list[tagging_result.TaggingResult]:
    """Specifies get operations."""
    converted_media_paths = [
      media.convert_path_to_media_name(media_path) for media_path in media_paths
    ]
    with self.session() as session:
      return [
        res.to_pydantic_model()
        for res in session.query(TaggingResults)
        .where(TaggingResults.identifier.in_(converted_media_paths))
        .all()
      ]

  def add(
    self,
    tagging_results: tagging_result.TaggingResult
    | Sequence[tagging_result.TaggingResult],
  ) -> None:
    """Specifies add operations."""
    with self.session() as session:
      for result in tagging_results:
        session.add(TaggingResults(**result.dict()))
      session.commit()

  def list(self) -> list[tagging_result.TaggingResult]:
    """Returns all tagging results from the repository."""
    with self.session() as session:
      return [
        res.to_pydantic_model() for res in session.query(TaggingResults).all()
      ]
