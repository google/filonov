# Copyright 2025 Google LLC
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

from filonov.creative_map import CreativeMap, MediaInfo
from media_similarity import media_similarity_service
from media_tagging import tagging_result


class TestCreativeMap:
  def test_to_json_returns_inferred_start_end_date(self):
    nodes = [
      {'name': 'test', 'series': {'2025-01-01': {'clicks': 1}}},
      {'name': 'test', 'series': {'2025-12-01': {'clicks': 1}}},
    ]
    creative_map = CreativeMap(adaptive_threshold=1, nodes=nodes)

    expected_json = {
      'graph': {
        'adaptive_threshold': 1,
        'period': {
          'start_date': '2025-01-01',
          'end_date': '2025-12-01',
        },
      },
      'clusters': {},
      'nodes': nodes,
      'edges': [],
    }

    assert creative_map.to_json() == expected_json

  def test_to_json_returns_null_start_end_date(self):
    nodes = [
      {'name': 'test'},
      {'name': 'test'},
    ]
    creative_map = CreativeMap(adaptive_threshold=1, nodes=nodes)

    expected_json = {
      'graph': {
        'adaptive_threshold': 1,
        'period': {
          'start_date': 'null',
          'end_date': 'null',
        },
      },
      'clusters': {},
      'nodes': nodes,
      'edges': [],
    }

    assert creative_map.to_json() == expected_json

  def test_from_clustering_returns_correct_map(self):
    adaptive_threshold = 1
    clusters = {'1': 1, '2': 2}
    nodes = [
      {'name': '1'},
      {'name': '2'},
    ]
    graph = media_similarity_service.GraphInfo(
      nodes=nodes,
      edges=[
        ('1', '2', 1),
      ],
    )
    clustering_results = media_similarity_service.ClusteringResults(
      clusters=clusters, adaptive_threshold=adaptive_threshold, graph=graph
    )
    tagging_results = [
      tagging_result.TaggingResult(
        identifier='test1',
        type='text',
        content=[tagging_result.Tag(name='test tag', score=1)],
        hash='1',
      ),
      tagging_result.TaggingResult(
        identifier='test2',
        type='text',
        content=[tagging_result.Tag(name='test tag', score=1)],
        hash='2',
      ),
    ]
    extra_info = {
      'test1': MediaInfo(
        media_path='test1',
        media_name='test1',
        info={'clicks': 10},
        series={'2025-01-01': {'clicks': 5}, '2025-12-01': {'clicks': 5}},
      ),
      'test2': MediaInfo(
        media_path='test2',
        media_name='test2',
        info={'clicks': 30},
        series={'2025-02-01': {'clicks': 15}, '2025-11-01': {'clicks': 15}},
      ),
    }
    creative_map = CreativeMap.from_clustering(
      clustering_results=clustering_results,
      tagging_results=tagging_results,
      extra_info=extra_info,
    )

    expected_edges = [{'from': '1', 'to': '2', 'similarity': 1}]
    expected_map = CreativeMap(
      adaptive_threshold=adaptive_threshold,
      nodes=clustering_results.graph.nodes,
      edges=expected_edges,
      clusters={
        cluster_id: f'Cluster: {cluster_id}'
        for media_hash, cluster_id in clusters.items()
      },
    )

    assert creative_map.to_json() == expected_map.to_json()
