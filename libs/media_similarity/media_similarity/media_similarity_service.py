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

import dataclasses
import itertools
from collections.abc import Iterable

import igraph
import pandas as pd
from media_tagging.taggers import base as base_tagger
from networkx.readwrite import json_graph

from media_similarity import adaptive_threshold, idf_context, media_pair


def _to_json(self):
  """Converts graph to JSON."""
  graph = json_graph.node_link_data(self.to_networkx(), edges='edges')
  return {
    'nodes': graph.get('nodes'),
    'edges': graph.get('links', []),
  }


igraph.Graph.to_json = _to_json


@dataclasses.dataclass
class ClusteringResults:
  """Contains results of clustering.

  Attributes:
    clusters: Mapping between media identifier and its cluster number.
    graph: Graph object used to perform clustering.
  """

  clusters: dict[str, int]
  graph: igraph.Graph


def cluster_media(
  tagging_results: Iterable[base_tagger.TaggingResult],
  normalize: bool = True,
  custom_threshold: float | None = None,
) -> ClusteringResults:
  """Assigns clusters number for each media.

  Args:
    tagging_results: Results of tagging used for clustering.
    normalize: Whether to normalize adaptive threshold.
    custom_threshold: Don't calculated adaptive threshold but use custom one.

  Returns:
     Results of clustering that contain mapping between media identifier.
  """
  idf_tag_context = idf_context.calculate_idf_context(tagging_results)
  similarity_pairs = (
    pair.calculate_similarity(idf_tag_context)
    for pair in media_pair.build_media_pairs(tagging_results)
  )
  [t1, t2] = itertools.tee(similarity_pairs, 2)
  if not custom_threshold:
    threshold = adaptive_threshold.compute_adaptive_threshold(
      similarity_scores=t1, normalize=normalize
    )
  else:
    threshold = adaptive_threshold.AdaptiveThreshold(
      custom_threshold, num_pairs=None
    )
  return _calculate_cluster_assignments(t2, threshold)


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
    if pair.similarity_score > threshold.threshold:
      similar_media.add(pair.to_tuple())

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
  return ClusteringResults(clusters=final_clusters, graph=graph)
