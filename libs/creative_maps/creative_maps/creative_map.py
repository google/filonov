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

import json
from collections.abc import Sequence
from typing import Any

from media_similarity import media_similarity_service
from media_tagging import tagging_result
from pyvis.network import Network

from creative_maps.inputs import interfaces


class CreativeMap:
  """Defines CreativeMap based on a graph.

  Attributes:
    graph: Network graph containing data for building a map.
    adaptive_threshold: Minimal value for defining similar media.
    fetching_request: Additional parameter used to generate a map.
  """

  def __init__(
    self,
    graph: Network,
    adaptive_threshold: float,
    fetching_request: dict[str, Any] | None = None,
  ) -> None:
    """Initializes CreativeMap."""
    self.graph = graph
    self.adaptive_threshold = adaptive_threshold
    self.fetching_request = fetching_request or {}

  @classmethod
  def from_clustering(
    cls,
    clustering_results: media_similarity_service.ClusteringResults,
    tagging_results: Sequence[tagging_result.TaggingResult],
    extra_info: dict[str, interfaces.MediaInfo] | None = None,
    fetching_request: dict[str, Any] | None = None,
  ) -> CreativeMap:
    """Builds network visualization with injected extra_info."""
    if not extra_info:
      extra_info = {}
    tagging_mapping = {
      result.identifier: result.content for result in tagging_results
    }
    g = Network()
    g.from_nx(clustering_results.graph.to_networkx())
    for node in g.nodes:
      node_name = node.get('name', '')
      if node_extra_info := extra_info.get(node_name):
        node['shape'] = 'image'
        node['type'] = 'image'
        node['image'] = node_extra_info.media_preview
        node['media_path'] = node_extra_info.media_path
        node['label'] = node_extra_info.media_name
        node['cluster'] = clustering_results.clusters.get(node_name)
        node['info'] = node_extra_info.info
        node['series'] = node_extra_info.series
        node['tags'] = [
          {'tag': tag.name, 'score': tag.score}
          for tag in tagging_mapping.get(node_name)
        ]
    return CreativeMap(
      g, clustering_results.adaptive_threshold, fetching_request
    )

  def to_json(self) -> dict[str, list[dict[str, str]]]:
    """Extracts nodes from Network."""

    def jsonify(value):
      return json.loads(value.replace('"', '').replace("'", '"'))

    res = json.loads(self.graph.to_json())
    return {
      'graph': {
        'adaptive_threshold': self.adaptive_threshold,
        'period': {
          'start_date': self.fetching_request.get('start_date', 'Unknown'),
          'end_date': self.fetching_request.get('end_date', 'Unknown'),
        },
      },
      'nodes': jsonify(res.get('nodes')),
      'edges': jsonify(res.get('edges')),
    }

  def export_html(self, output: str) -> None:
    """Exports map to html file."""
    self.graph.save_graph(output)
