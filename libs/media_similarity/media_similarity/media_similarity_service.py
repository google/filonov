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
"""Responsible for performing media clustering."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

import itertools
import logging
import os
from collections.abc import Iterable, Sequence
from concurrent import futures
from typing import Final

import igraph
import media_tagging
import pandas as pd
import pydantic
from garf_core import report

from media_similarity import (
  adaptive_threshold,
  exceptions,
  idf_context,
  media_pair,
  repositories,
)

BATCH_SIZE: Final[int] = 1_000


logger = logging.getLogger('media-similarity')


def _batched(iterable: Iterable[media_pair.MediaPair], chunk_size: int):
  iterator = iter(iterable)
  while chunk := tuple(itertools.islice(iterator, chunk_size)):
    yield chunk


class GraphInfo(pydantic.BaseModel):
  """Stores information of media and their relationships."""

  nodes: list[dict[str, str]]
  edges: set[tuple[str, str, float]]


class MediaClusteringRequest(pydantic.BaseModel):
  """Specifies structure of request for clustering media.

  Attributes:
    media_paths: Identifiers or media to cluster (file names or links).
    media_type: Type of media found in media_paths.
    tagger_type: Type of tagger to use if media tags are not found.
    normalize: Whether to apply normalization threshold.
  """

  media_paths: list[str]
  media_type: str
  tagger_type: str | None = 'gemini'
  normalize: bool = True


class ClusteringResults(pydantic.BaseModel):
  """Contains results of clustering.

  Attributes:
    clusters: Mapping between media identifier and its cluster number.
    adaptive_threshold: Minimal value for defining similar media.
    graph: Mapping with nodes and edges.
  """

  clusters: dict[str, int]
  adaptive_threshold: float
  graph: GraphInfo

  def to_garf_report(self) -> report.GarfReport:
    """Converts clusters to flattend report."""
    results = []
    for media_url, cluster_id in self.clusters.items():
      results.append([cluster_id, media_url])
    return report.GarfReport(results, column_names=['cluster_id', 'media_url'])


class MediaSimilaritySearchRequest(pydantic.BaseModel):
  """Request for performing similarity search.

  Attributes:
    media_paths: Paths to media intended for search.
    media_type: Types of media to find.
    n_results: Maximum number of results to return for each media path.
  """

  media_paths: list[os.PathLike[str] | str] | str
  media_type: str = 'UNKNOWN'
  n_results: int = 10

  def model_post_init(self, __context__) -> None:
    if isinstance(self.media_paths, str):
      self.media_paths = [self.media_paths]

  @property
  def media_identifiers(self) -> set[str]:
    """Normalized media identifiers based on media type."""
    return {
      media_tagging.media.convert_path_to_media_name(
        media_path, self.media_type
      )
      for media_path in self.media_paths
    }


class SimilaritySearchResults(pydantic.BaseModel):
  """Contains results of similarity search.

  Attributes:
    seed_media_identifier: Media identifier used to perform a search.
    results: Identifiers of the most similar media with their similarity scores.
  """

  seed_media_identifier: str
  results: dict[str, float]

  def to_garf_report(self) -> report.GarfReport:
    """Converts to flattened report."""
    results = []
    for k, v in self.results.items():
      results.append([self.seed_media_identifier, k, v])
    return report.GarfReport(
      results,
      column_names=['seed_media_identifier', 'media_identifier', 'score'],
    )


class MediaSimilarityComparisonRequest(pydantic.BaseModel):
  """Request for performing media comparison.

  Attributes:
    media_paths: Paths to media intended for search.
    media_type: Types of media to find.
  """

  media_paths: list[os.PathLike[str] | str]
  media_type: str = 'UNKNOWN'

  @property
  def media_identifiers(self) -> set[str]:
    """Normalized media identifiers based on media type."""
    return {
      media_tagging.media.convert_path_to_media_name(
        media_path, self.media_type
      )
      for media_path in self.media_paths
    }


class MediaSimilarityComparisonResult(pydantic.BaseModel):
  """Contains results of media similarity comparison.

  Attributes:
    media_pair_identifier: Media identifier used to perform comparison.
    similarity_score: Similarity score between media.
  """

  media_pair_identifier: str
  similarity_score: media_pair.SimilarityScore

  def to_garf_report(self) -> report.GarfReport:
    """Converts to flattened report."""
    return report.GarfReport(
      [
        [
          self.media_pair_identifier,
          self.similarity_score.score,
          self.similarity_score.similarity_weight.n_tags,
          self.similarity_score.similarity_weight.normalized_value,
          self.similarity_score.similarity_weight.unnormalized_value,
          self.similarity_score.dissimilarity_weight.n_tags,
          self.similarity_score.dissimilarity_weight.normalized_value,
          self.similarity_score.dissimilarity_weight.unnormalized_value,
        ]
      ],
      column_names=[
        'media_pair_identifier',
        'score',
        'similar_tags',
        'similarity_weight_normalized',
        'similarity_weight_unnormalized',
        'dissimilar_tags',
        'dissimilarity_weight_normalized',
        'dissimilarity_weight_unnormalized',
      ],
    )


def _create_similarity_pairs(
  pairs: Sequence[media_pair.MediaPair],
  idf_tag_context: idf_context.IdfContext,
  batch_idx: int,
  total_batches: int,
) -> list[media_pair.SimilarityPair]:
  logger.info('processing index %d of %d', batch_idx, total_batches)
  return [pair.calculate_similarity(idf_tag_context) for pair in pairs]


class MediaSimilarityService:
  """Handles tasks related to media similarity.

  Attributes:
    repo: Repository that contains similarity pairs.
  """

  def __init__(
    self,
    media_similarity_repository: repositories.BaseSimilarityPairsRepository,
  ) -> None:
    """Initializes MediaSimilarityService."""
    self.repo = media_similarity_repository

  @classmethod
  def from_connection_string(cls, db_uri: str) -> MediaSimilarityService:
    """Builds service based on a DB connection string."""
    repo = repositories.SqlAlchemySimilarityPairsRepository(db_uri)
    repo.initialize()
    return MediaSimilarityService(repo)

  def cluster_media(
    self,
    tagging_results: Sequence[media_tagging.tagging_result.TaggingResult],
    normalize: bool = True,
    custom_threshold: float | None = None,
    parallel_threshold: int = 10,
  ) -> ClusteringResults:
    """Assigns clusters number for each media.

    Args:
      tagging_results: Results of tagging used for clustering.
      normalize: Whether to normalize adaptive threshold.
      custom_threshold: Don't calculated adaptive threshold but use custom one.
      parallel_threshold: Max number of parallel executions.

    Returns:
       Results of clustering that contain mapping between media identifier.

    Raises:
      MediaSimilarityError: When not tagging results were found.
    """
    if not tagging_results:
      raise exceptions.MediaSimilarityError('No tagging results found.')
    tagger = tagging_results[0].tagger
    logger.info('calculating context...')
    idf_tag_context = idf_context.calculate_idf_context(tagging_results)
    similarity_pairs = []
    logger.info('generating media pairs...')
    media_pairs = list(media_pair.build_media_pairs(tagging_results))
    uncalculated_media_pairs = media_pairs
    calculated_similarity_pairs = []
    if self.repo and (
      calculated_similarity_pairs := self.repo.get(media_pairs, tagger)
    ):
      calculated_similarity_pairs_keys = {
        pair.key for pair in calculated_similarity_pairs
      }
      uncalculated_media_pairs = [
        pair
        for pair in media_pairs
        if str(pair) not in calculated_similarity_pairs_keys
      ]

    if not uncalculated_media_pairs:
      logger.info('calculating threshold...')
      if not custom_threshold:
        threshold = adaptive_threshold.compute_adaptive_threshold(
          similarity_scores=calculated_similarity_pairs, normalize=normalize
        )
      else:
        threshold = adaptive_threshold.AdaptiveThreshold(
          custom_threshold, num_pairs=None
        )
      logger.info('threshold is %.2f', threshold.threshold)
      logger.info('assigning clusters...')
      return _calculate_cluster_assignments(
        calculated_similarity_pairs, threshold
      )
    if parallel_threshold > 1:
      total_batches = len(uncalculated_media_pairs)
      total_batches = (
        total_batches // BATCH_SIZE
        if total_batches % BATCH_SIZE == 0
        else total_batches // BATCH_SIZE + 1
      )

      logger.info('calculating similarity...')
      logger.debug(
        'running similarity calculation for %s batches (to process %s pairs '
        'in total)',
        total_batches,
        len(uncalculated_media_pairs),
      )

      with futures.ThreadPoolExecutor(
        max_workers=parallel_threshold
      ) as executor:
        future_to_batch = {
          executor.submit(
            _create_similarity_pairs,
            batch,
            idf_tag_context,
            batch_index,
            total_batches,
          ): batch_index
          for batch_index, batch in enumerate(
            _batched(uncalculated_media_pairs, BATCH_SIZE), 1
          )
        }
        for future in futures.as_completed(future_to_batch):
          processed_batch = future.result()
          similarity_pairs.append(processed_batch)
          if self.repo:
            self.repo.add(processed_batch)
      similarity_pairs = list(itertools.chain.from_iterable(similarity_pairs))
      similarity_pairs = similarity_pairs + calculated_similarity_pairs
    else:
      logger.info('calculating similarity...')
      similarity_pairs = [
        pair.calculate_similarity(idf_tag_context)
        for pair in uncalculated_media_pairs
      ]
      if self.repo:
        self.repo.add(similarity_pairs)

    logger.info('calculating threshold...')
    if not custom_threshold:
      threshold = adaptive_threshold.compute_adaptive_threshold(
        similarity_scores=similarity_pairs, normalize=normalize
      )
    else:
      threshold = adaptive_threshold.AdaptiveThreshold(
        custom_threshold, num_pairs=None
      )
    logger.info('threshold is %.2f', threshold.threshold)
    logger.info('assigning clusters...')
    return _calculate_cluster_assignments(similarity_pairs, threshold)

  def find_similar_media(
    self,
    request: MediaSimilaritySearchRequest,
  ) -> list[SimilaritySearchResults]:
    """Finds top similar media for multiple seed media identifiers.

    Args:
      request: Similarity search request.

    Returns:
      Similar media for each seed identifier.
    """
    return [
      self._find_similar_media(identifier, request.n_results)
      for identifier in request.media_identifiers
    ]

  def _find_similar_media(
    self,
    seed_media_identifier: os.PathLike[str] | str,
    n_results: int = 10,
  ) -> SimilaritySearchResults:
    """Finds top similar media for a given seed media identifier."""
    similar_media = self.repo.get_similar_media(
      identifier=seed_media_identifier, n_results=n_results
    )
    media_identifiers = {}
    for pair in similar_media:
      for medium in pair.media:
        if medium != seed_media_identifier:
          media_identifiers[medium] = pair.similarity_score.score
    return SimilaritySearchResults(
      seed_media_identifier=seed_media_identifier, results=media_identifiers
    )

  def compare_media(
    self,
    request: MediaSimilarityComparisonRequest,
  ) -> list[MediaSimilarityComparisonResult]:
    """Returns results of similarity detection between pair of media.

    Args:
     request: Similarity comparison request.

    Returns:
      Sequence of results of comparison.
    """
    results = []
    for media_identifier_1, media_identifier_2 in itertools.combinations(
      request.media_identifiers, 2
    ):
      if media_identifier_1 != media_identifier_2:
        key = (
          f'{media_identifier_1}|{media_identifier_2}'
          if media_identifier_1 < media_identifier_2
          else f'{media_identifier_2}|{media_identifier_1}'
        )
        if not (similarity_pair := self.repo.get([key])):
          continue
        results.append(
          MediaSimilarityComparisonResult(
            media_pair_identifier=key,
            similarity_score=similarity_pair[0].similarity_score,
          )
        )
    return results


def _calculate_cluster_assignments(
  similarity_pairs: Iterable[media_pair.SimilarityPair],
  threshold: adaptive_threshold.AdaptiveThreshold,
) -> ClusteringResults:
  """Assigns cluster number for each media in similarity pairs.

  All media with similarity score greater than threshold are considered similar.
  All media with similarity score lower than threshold are considered dissimilar
  and get its own unique cluster_id.

  Args:
    similarity_pairs: Mapping between media_pair identifier and
      its similarity score.
    threshold: Threshold to identify similar media.

  Returns:
     Results of clustering that contain mapping between media identifier and
     its cluster number as well as graph.
  """
  media: set[str] = set()
  similar_media: set[tuple[str, str, float]] = set()
  for pair in similarity_pairs:
    media_1, media_2 = pair.media
    media.add(media_1)
    media.add(media_2)
    if pair.similarity_score.score > threshold.threshold:
      similar_media.add(pair.to_tuple())

  nodes = [{'name': node} for node in media]
  graph = igraph.Graph.DataFrame(
    edges=pd.DataFrame(
      similar_media, columns=['media_1', 'media_2', 'similarity']
    ),
    directed=False,
    use_vids=False,
    vertices=pd.DataFrame(media, columns=['media']),
  )
  final_clusters: dict[str, int] = {}
  clusters = graph.community_walktrap().as_clustering()
  for i, cluster_media in enumerate(clusters._formatted_cluster_iterator(), 1):
    for media in cluster_media.split(', '):
      final_clusters[media] = i
  return ClusteringResults(
    clusters=final_clusters,
    adaptive_threshold=threshold.threshold,
    graph=GraphInfo(nodes=nodes, edges=similar_media),
  )
