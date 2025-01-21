# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Builds Creative Maps network."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypedDict

from media_similarity import media_similarity_service
from media_tagging import tagging_result

from filonov.inputs import interfaces


class GraphInfo(TypedDict):
  adaptive_threshold: float
  period: dict[str, str]


class ClusterInfo(TypedDict):
  name: str


class NodeInfo(TypedDict):
  name: str
  label: str
  type: str
  image: str
  media_path: str
  cluster: int
  info: interfaces.Info
  series: dict[str, interfaces.MetricInfo]
  tags: list[dict[str, float]]
  segments: dict[str, str]


class CreativeMapJson(TypedDict):
  graph: GraphInfo
  clusters: dict[int, ClusterInfo]
  nodes: list[NodeInfo]
  edges: list[dict[str, int | float]]


class CreativeMap:
  """Defines CreativeMap based on a graph.

  Attributes:
    adaptive_threshold: Minimal value for defining similar media.
    fetching_request: Additional parameter used to generate a map.
    nodes: Information on each node of the map.
    edges: Information on each edge of the map.
    clusters: Aggregated information on each cluster of the map.
  """

  def __init__(
    self,
    adaptive_threshold: float,
    fetching_request: dict[str, Any] | None = None,
    nodes: list[NodeInfo] | None = None,
    edges: list[dict[str, int | float]] | None = None,
    clusters: dict[int, ClusterInfo] | None = None,
  ) -> None:
    """Initializes CreativeMap."""
    self.adaptive_threshold = adaptive_threshold
    self.fetching_request = fetching_request or {}
    self.nodes: list[NodeInfo] = nodes or []
    self.edges: list[dict[str, int | float]] = edges or []
    self.clusters: dict[int, ClusterInfo] = clusters or {}

  @classmethod
  def from_clustering(
    cls,
    clustering_results: media_similarity_service.ClusteringResults,
    tagging_results: Sequence[tagging_result.TaggingResult],
    extra_info: dict[str, interfaces.MediaInfo] | None = None,
    fetching_request: dict[str, Any] | None = None,
  ) -> CreativeMap:
    """Builds network visualization with injected extra_info."""
    tagging_mapping = {
      result.identifier: result.content for result in tagging_results
    }
    for node in clustering_results.graph.nodes:
      node_name = node.get('name', '')
      if node_extra_info := extra_info.get(node_name):
        node['id'] = node_name
        if size := node_extra_info.size:
          node['size'] = size
        node['type'] = 'image'
        node['image'] = node_extra_info.media_preview
        node['media_path'] = node_extra_info.media_path
        node['label'] = node_extra_info.media_name
        node['cluster'] = clustering_results.clusters.get(node_name)
        node['info'] = node_extra_info.info
        node['series'] = node_extra_info.series
        node['tags'] = [
          {'tag': tag.name.replace("'", ''), 'score': tag.score}
          for tag in tagging_mapping.get(node_name, [])
        ]
        node['segments'] = node_extra_info.segments
    clusters = {
      cluster_id: f'Cluster: {cluster_id}'
      for cluster_id in set(clustering_results.clusters.values())
    }
    edges = [
      {
        'from': _from,
        'to': to,
        'similarity': similarity,
      }
      for _from, to, similarity in clustering_results.graph.edges
    ]
    return CreativeMap(
      adaptive_threshold=clustering_results.adaptive_threshold,
      fetching_request=fetching_request,
      nodes=clustering_results.graph.nodes,
      edges=edges,
      clusters=clusters,
    )

  def to_json(self) -> CreativeMapJson:
    """Extracts nodes from Network."""
    return {
      'graph': {
        'adaptive_threshold': self.adaptive_threshold,
        'period': {
          'start_date': self.fetching_request.get('start_date', 'null'),
          'end_date': self.fetching_request.get('end_date', 'null'),
        },
      },
      'clusters': self.clusters,
      'nodes': self.nodes,
      'edges': self.edges,
    }
