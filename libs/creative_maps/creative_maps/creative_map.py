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

import dataclasses
import json
import os
import pickle
from collections.abc import Sequence

from media_similarity import media_similarity_service
from media_tagging import tagging_result
from pyvis.network import Network

from creative_maps.inputs import interfaces


class CreativeMap:
  """Defines CreativeMap based on a graph.

  Attributes:
    graph: Network graph containing data for building a map.
  """

  def __init__(self, graph: Network) -> None:
    """Initializes CreativeMap."""
    self.graph = graph

  @classmethod
  def load(cls, path: os.PathLike[str]) -> CreativeMap:
    """Loads map to pickle."""
    with open(path, 'rb') as f:
      graph = pickle.load(f)
    return CreativeMap(graph)

  @classmethod
  def from_clustering(
    cls,
    clustering_results: media_similarity_service.ClusteringResults,
    tagging_results: Sequence[tagging_result.TaggingResult],
    extra_info: dict[str, interfaces.MediaInfo] | None = None,
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
        node['image'] = node_extra_info.media_path
        node['media_path'] = node_extra_info.media_path
        node['label'] = node_extra_info.media_name
        node['cluster'] = clustering_results.clusters.get(node_name)
        node['info'] = dataclasses.asdict(node_extra_info)
        node['tags'] = [
          {'tag': tag.name, 'score': tag.score}
          for tag in tagging_mapping.get(node_name)
        ]
    return CreativeMap(g)

  def to_json(self) -> dict[str, list[dict[str, str]]]:
    """Extracts nodes from Network."""

    def jsonify(value):
      return json.loads(value.replace('"', '').replace("'", '"'))

    res = json.loads(self.graph.to_json())
    return {
      'nodes': jsonify(res.get('nodes')),
      'edges': jsonify(res.get('edges')),
    }

  def save(self, path: os.PathLike[str]) -> None:
    """Saves map to pickle."""
    with open(path, 'wb') as f:
      pickle.dump(self.graph, f)

  def export_json(self, output: str) -> None:
    """Exports nodes and edges to json."""
    with open(output, 'w', encoding='utf-8') as f:
      json.dump(self.to_json(), f)

  def export_html(self, output: str) -> None:
    """Exports map to html file."""
    self.graph.save_graph(output)
