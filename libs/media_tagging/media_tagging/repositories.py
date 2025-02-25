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
from collections.abc import Sequence

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
from typing_extensions import override

from media_tagging import media, tagging_result


class BaseTaggingResultsRepository(abc.ABC):
  """Interface for defining repositories."""

  @abc.abstractmethod
  def get(
    self, media_paths: str | Sequence[str], media_type: media.MediaTypeEnum
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


class InMemoryTaggingResultsRepository(BaseTaggingResultsRepository):
  """Uses pickle files for persisting tagging results."""

  def __init__(self) -> None:
    """Initializes InMemoryTaggingResultsRepository."""
    self.results = []

  @override
  def get(
    self, media_paths: Sequence[str], media_type: media.MediaTypeEnum
  ) -> list[tagging_result.TaggingResult]:
    converted_media_paths = [
      media.convert_path_to_media_name(media_path, media_type)
      for media_path in media_paths
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
  processed_at = sqlalchemy.Column(sqlalchemy.DateTime)
  identifier = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  output = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  tagger = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  type = sqlalchemy.Column(sqlalchemy.String(10), primary_key=True)
  content = sqlalchemy.Column(sqlalchemy.JSON)
  tagging_details = sqlalchemy.Column(sqlalchemy.JSON)

  def to_pydantic_model(self) -> tagging_result.TaggingResult:
    """Converts model to pydantic object."""
    return tagging_result.TaggingResult(
      processed_at=self.processed_at,
      identifier=self.identifier,
      type=self.type,
      content=self.content,
      output=self.output,
      tagger=self.tagger,
      tagging_details=self.tagging_details,
    )


class SqlAlchemyRepository:
  """Mixin class for common functionality in SqlAlchemy based repositories."""

  IN_MEMORY_DB = 'sqlite://'

  def __init__(self, db_url: str | None = None) -> None:
    """Initializes SqlAlchemyTaggingResultsRepository."""
    self.db_url = db_url or self.IN_MEMORY_DB
    self.initialized = False
    self._engine = None

  def initialize(self) -> None:
    """Creates all ORM objects."""
    self.initialized = True

  @property
  def session(self) -> sqlalchemy.orm.sessionmaker[sqlalchemy.orm.Session]:
    """Property for initializing session."""
    if not self.initialized:
      self.initialize()
    return sqlalchemy.orm.sessionmaker(bind=self.engine)

  @property
  def engine(self) -> sqlalchemy.engine.Engine:
    """Initialized SQLalchemy engine."""
    if self._engine:
      return self._engine
    if self.db_url == self.IN_MEMORY_DB:
      self._engine = sqlalchemy.create_engine(
        self.db_url,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
      )
    else:
      self._engine = sqlalchemy.create_engine(self.db_url)
    return self._engine


class SqlAlchemyTaggingResultsRepository(
  BaseTaggingResultsRepository, SqlAlchemyRepository
):
  """Uses SqlAlchemy engine for persisting tagging results."""

  def initialize(self) -> None:
    """Creates all ORM objects."""
    Base.metadata.create_all(self.engine)
    super().initialize()

  def get(
    self,
    media_paths: str | Sequence[str],
    media_type: str,
    tagger_type: str,
    output: str,
  ) -> list[tagging_result.TaggingResult]:
    """Specifies get operations."""
    converted_media_paths = [
      media.convert_path_to_media_name(media_path, media_type)
      for media_path in media_paths
    ]
    with self.session() as session:
      return [
        res.to_pydantic_model()
        for res in session.query(TaggingResults)
        .where(
          TaggingResults.identifier.in_(converted_media_paths),
          TaggingResults.output == output,
          TaggingResults.tagger == tagger_type,
        )
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
