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
import collections
import hashlib
import itertools
import json
from collections.abc import Sequence

import sqlalchemy
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.pool import StaticPool
from typing_extensions import override

from media_tagging import media, tagging_result


class BaseTaggingResultsRepository(abc.ABC):
  """Interface for defining repositories."""

  @abc.abstractmethod
  def get(
    self,
    media_paths: str | Sequence[str],
    media_type: str,
    tagger_type: str | None = None,
    output: str | None = None,
    deduplicate: bool = False,
    tagging_details: dict[str, str] | None = None,
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
    self,
    media_paths: str | Sequence[str],
    media_type: str,
    tagger_type: str | None = None,
    output: str | None = None,
    deduplicate: bool = False,
    tagging_details: dict[str, str] | None = None,
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


class TaggingDetails(Base):
  """ORM model for persisting TaggingDetails."""

  __tablename__ = 'tagging_details'
  id = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)
  content = sqlalchemy.Column(sqlalchemy.JSON)

  info = relationship('TaggingResults', back_populates='tagging_details')


class Identifiers(Base):
  """ORM model for persisting Identifier mapping."""

  __tablename__ = 'identifiers'
  hash = sqlalchemy.Column(sqlalchemy.String(32), primary_key=True)
  content = sqlalchemy.Column(sqlalchemy.Text)

  tagging_content = relationship('TaggingResults', back_populates='identifier')


class TaggingResults(Base):
  """ORM model for persisting TaggingResult."""

  __tablename__ = 'tagging_results'
  processed_at = sqlalchemy.Column(sqlalchemy.DateTime, primary_key=True)
  hash = sqlalchemy.Column(
    sqlalchemy.String(32),
    sqlalchemy.ForeignKey('identifiers.hash'),
    primary_key=True,
  )
  output = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  tagger = sqlalchemy.Column(sqlalchemy.String(255), primary_key=True)
  type = sqlalchemy.Column(sqlalchemy.String(10), primary_key=True)
  content = sqlalchemy.Column(sqlalchemy.JSON)

  tagging_details_id = sqlalchemy.Column(
    sqlalchemy.String(32),
    sqlalchemy.ForeignKey('tagging_details.id'),
    primary_key=True,
  )
  tagging_details = relationship('TaggingDetails', back_populates='info')
  identifier = relationship('Identifiers', back_populates='tagging_content')

  def to_pydantic_model(self) -> tagging_result.TaggingResult:
    """Converts model to pydantic object."""
    return tagging_result.TaggingResult(
      processed_at=self.processed_at,
      identifier=self.identifier.content,
      type=self.type,
      content=self.content,
      output=self.output,
      tagger=self.tagger,
      tagging_details=self.tagging_details.content,
      hash=self.hash,
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
    tagger_type: str | None = None,
    output: str | None = None,
    deduplicate: bool = False,
    tagging_details: dict[str, str] | None = None,
  ) -> list[tagging_result.TaggingResult]:
    """Specifies get operations."""
    if isinstance(media_paths, str):
      media_paths = [media_paths]
    all_media = [
      media.Medium(media_path=media_path, media_type=media_type)
      for media_path in media_paths
    ]
    media_hashes = []
    for m in all_media:
      try:
        media_hashes.append(m.identifier)
      except media.InvalidMediaPathError:
        continue
    if not media_hashes:
      return []
    with self.session() as session:
      query = session.query(TaggingResults).where(
        TaggingResults.hash.in_(media_hashes)
      )
      if output:
        query = query.where(TaggingResults.output == output)
      if tagger_type:
        query = query.where(TaggingResults.tagger == tagger_type)
      if tagging_details:
        tagging_details_hash = hashlib.md5(
          json.dumps(tagging_details).encode('utf-8')
        ).hexdigest()
        query = query.where(
          TaggingResults.tagging_details_id == tagging_details_hash
        )

      if not (results := query.all()):
        return []
      tagging_results = [res.to_pydantic_model() for res in results]
      if not deduplicate:
        return tagging_results
      dedup = collections.defaultdict(list)
      for result in tagging_results:
        dedup[result.hash].append(result.content)
      hash_to_identifier_mapping = {
        t.hash: t.identifier for t in tagging_results
      }
      final_results = []
      for hash, identifier in hash_to_identifier_mapping.items():
        if output == 'tag':
          content = set(itertools.chain(*dedup[hash]))
        else:
          content = list(set(dedup[hash]))
        final_results.append(
          tagging_result.TaggingResult(
            identifier=identifier,
            type=media_type.lower(),
            tagger=tagger_type,
            output=output if output == 'tag' else 'description',
            content=content,
            hash=hash,
          )
        )
      return final_results

  def add(
    self,
    tagging_results: tagging_result.TaggingResult
    | Sequence[tagging_result.TaggingResult],
  ) -> None:
    """Specifies add operations."""
    if isinstance(tagging_results, tagging_result.TaggingResult):
      tagging_results = [tagging_results]
    with self.session() as session:
      identifiers = [t.hash for t in tagging_results]
      tagging_details = [
        hashlib.md5(json.dumps(t.tagging_details).encode('utf-8')).hexdigest()
        for t in tagging_results
      ]
      ids = [
        i.hash
        for i in session.query(Identifiers)
        .where(Identifiers.hash.in_(identifiers))
        .all()
      ]
      tagging_details_ids = [
        t.id
        for t in session.query(TaggingDetails)
        .where(TaggingDetails.id.in_(tagging_details))
        .all()
      ]
      for result in tagging_results:
        content = (
          [r.model_dump() for r in result.content]
          if isinstance(result.content, tuple)
          else result.content.model_dump()
        )
        tagging_results_orm = TaggingResults(
          processed_at=result.processed_at,
          hash=result.hash,
          tagger=result.tagger,
          output=result.output,
          type=result.type,
          content=content,
        )
        if tagging_results_orm.hash not in ids:
          tagging_results_orm.identifier = Identifiers(
            hash=tagging_results_orm.hash, content=result.identifier
          )
          ids.append(tagging_results_orm.hash)
        if (
          tagging_details_hash := hashlib.md5(
            json.dumps(result.tagging_details).encode('utf-8')
          ).hexdigest()
        ) in tagging_details_ids:
          tagging_results_orm.tagging_details_id = tagging_details_hash
        else:
          tagging_results_orm.tagging_details = TaggingDetails(
            id=tagging_details_hash,
            content=result.tagging_details,
          )
          tagging_details_ids.append(tagging_details_hash)
        session.add(tagging_results_orm)
      session.commit()

  def list(self) -> list[tagging_result.TaggingResult]:
    """Returns all tagging results from the repository."""
    with self.session() as session:
      return [
        res.to_pydantic_model() for res in session.query(TaggingResults).all()
      ]
