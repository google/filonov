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
import logging
import operator
import os
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias, TypedDict

import numpy as np
import pydantic
import smart_open
from garf_core import report
from media_similarity import media_similarity_service
from media_tagging import media, tagging_result
from opentelemetry import trace

from filonov import previews
from filonov.telemetry import tracer

MetricInfo: TypeAlias = dict[str, int | float]
Info: TypeAlias = dict[str, int | float | str | list[str] | None]


class MediaInfo(pydantic.BaseModel):
  """Contains extra information on a given medium."""

  media_path: str
  media_name: str
  info: Info
  series: dict[str, MetricInfo]
  media_preview: str | None = None
  size: float | None = None
  segments: dict[str, dict[str, Info]] | None = None

  def model_post_init(self, __context__) -> None:  # noqa: D105
    if not self.media_preview:
      self.media_preview = self.media_path
    self.info = dict(self.info)


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
  info: Info
  series: dict[str, MetricInfo]
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
  @tracer.start_as_current_span('create_map')
  def from_clustering(
    cls,
    clustering_results: media_similarity_service.ClusteringResults,
    tagging_results: Sequence[tagging_result.TaggingResult],
    extra_info: dict[str, MediaInfo] | None = None,
    fetching_request: dict[str, Any] | None = None,
    embed_previews: bool = False,
  ) -> CreativeMap:
    """Builds network visualization with injected extra_info."""
    tagging_mapping = {
      result.identifier: result.content for result in tagging_results
    }
    tagging_hash_to_identifier_mapping = {
      t.hash: t.identifier for t in tagging_results
    }
    media_type = tagging_results[0].type
    preview_strategy = previews.get_media_preview_strategy(
      media_type=media_type, embed_previews=embed_previews
    )
    for node in clustering_results.graph.nodes:
      node_hash = node.get('name', '')
      node_name = tagging_hash_to_identifier_mapping.get(node_hash)
      if node_extra_info := extra_info.get(node_name):
        node['id'] = node_hash
        if size := node_extra_info.size:
          node['size'] = size
        node['type'] = media_type
        if preview_strategy:
          node['image'] = preview_strategy(node_extra_info)
        else:
          node['image'] = node_extra_info.media_preview
        node['media_path'] = node_extra_info.media_path
        node['label'] = node_extra_info.media_name or 'Unknown'
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
    start_date = ''
    end_date = ''
    for node in self.nodes:
      if series := node.get('series'):
        min_start_date = min(series.keys())
        max_end_date = max(series.keys())
        if not start_date or min_start_date < start_date:
          start_date = min_start_date
        if not end_date or max_end_date > end_date:
          end_date = max_end_date

    return {
      'graph': {
        'adaptive_threshold': self.adaptive_threshold,
        'period': {
          'start_date': start_date or 'null',
          'end_date': end_date or 'null',
        },
      },
      'clusters': self.clusters,
      'nodes': self.nodes,
      'edges': self.edges,
    }

  @tracer.start_as_current_span('save')
  def save(self, path: str | os.PathLike[str]) -> None:
    """Saves map to a json file."""
    span = trace.get_current_span()
    span.set_attribute('filonov.creative_map.path', str(path))
    with smart_open.open(path, 'w', encoding='utf-8') as f:
      json.dump(self.to_json(), f)


@tracer.start_as_current_span('convert_report_to_media_info')
def convert_report_to_media_info(
  performance: report.GarfReport,
  media_type: media.MediaTypeEnum,
  metric_columns: Sequence[str] | None = None,
  segment_columns: Sequence[str] | None = None,
  modules: Sequence[str] | None = None,
  with_size_base: str | None = None,
  omit_time_series: bool = False,
) -> dict[str, MediaInfo]:
  """Convert report to MediaInfo mappings.

  Args:
    performance: Report with media data.
    media_type: Type of media in the report.
    metric_columns:  Name of metrics to be included in media info.
    segment_columns:  Name of segments to be calculated.
    modules: Optional column names to be added to media_info.
    with_size_base: Optional column name for regulating size of media info.
    omit_time_series: Whether to exclude time series data from media info.

  Returns:
    Mapping between media identifier and its media info.
  """
  if isinstance(media_type, str):
    media_type = media.MediaTypeEnum[media_type.upper()]
  if with_size_base and with_size_base not in performance.column_names:
    logging.warning('Failed to set MediaInfo size to %s', with_size_base)
    with_size_base = None
  if with_size_base:
    try:
      float(performance[0][with_size_base])
    except TypeError:
      logging.warning('MediaInfo size attribute should be numeric')
    with_size_base = None

  if modules:
    modules = {module.split('.')[1] for module in modules}
    modules = modules.intersection(performance.column_names)
  else:
    modules = set()

  if media_type == media.MediaTypeEnum.YOUTUBE_VIDEO:
    modules.add('duration')
    modules.add('orientation')
  elif media_type == media.MediaTypeEnum.IMAGE:
    modules.add('format_type')

  metric_columns = metric_columns or []
  if 'in_campaigns' in performance.column_names:
    modules.add('in_campaigns')

  results = {}
  for media_url, values in performance.to_dict(key_column='media_url').items():
    info = build_info(values, list(metric_columns), list(modules))
    segments = (
      build_segments(values, segment_columns, metric_columns)
      if segment_columns
      else {}
    )
    if values[0].get('date') and not omit_time_series:
      series = build_segments(values, ['date'], metric_columns).get('date', {})
    else:
      series = {}
    if with_size_base and (size_base := info.get(with_size_base)):
      media_size = np.log(size_base) * np.log10(size_base)
    else:
      media_size = None
    results[media.convert_path_to_media_name(media_url, media_type)] = (
      MediaInfo(
        **create_node_links(media_url, media_type),
        media_name=values[0].get('media_name'),
        info=info,
        series=series,
        size=media_size,
        segments=segments,
      )
    )
  return results


def build_info(
  data: Info, metric_names: Sequence[str], modules: Sequence[str] | None = None
) -> Info:
  """Extracts and aggregated data for specified metrics.

  Args:
    data: All available information on media_url.
    metric_names: Metrics to sum.
    modules: Meterics/ dimensions to get as is without aggregation.

  Returns:
    Mapping between name of metric / dimension and its processed value.
  """
  info = {
    metric: _aggregate_nested_metric(data, metric) for metric in metric_names
  }
  if modules:
    dimensions = {module: data[0].get(module) for module in modules}
    info.update(dimensions)
  return info


def build_segments(
  data: Info, segment_names: Sequence[str], metric_names: Sequence[str]
) -> dict[str, dict[Info]]:
  """Builds info object for each variant of a segment.

  Args:
    data: Report data formatted as a mapping.
    segment_names: Names of column in report to transform into segments.
    metric_names: Names of metrics in report to calculate for each segment.

  Returns:
    Mapping between each segment, it's variants and corresponding metrics.
  """
  segments = {}
  for segment_name in segment_names:
    get_segment_getter = operator.itemgetter(segment_name)
    try:
      segment_values = set(map(get_segment_getter, data))
    except KeyError:
      continue
    segment_variants = {}
    for segment_value in segment_values:
      if segment_value != 'UNKNOWN':
        segment_variants[segment_value] = build_info(
          list(filter(lambda x: x[segment_name] == segment_value, data)),
          metric_names,
        )
    if segment_variants:
      segments[segment_name] = segment_variants
  return segments


def _aggregate_nested_metric(
  data: Info | Sequence[Info],
  metric_name: str,
) -> float | int | str | list[str] | None:
  """Performance appropriate aggregation over a dictionary.

  Sums numerical values and deduplicates and sorts alphabetically
  string values.

  Args:
    data: Data to extract metrics from.
    metric_name: Name of a metric to be extracted from supplied data.

  Returns:
    Aggregated value of a metric.
  """
  get_metric_getter = operator.itemgetter(metric_name)
  if isinstance(data, Mapping):
    return get_metric_getter(data)

  try:
    res = list(map(get_metric_getter, data))
  except KeyError:
    return None
  try:
    return sum(res)
  except TypeError:
    if len(result := sorted(set(res))) == 1:
      return ','.join(result)
    return result


def create_node_links(
  url: str, media_type: media.MediaTypeEnum
) -> dict[str, str]:
  return {
    'media_path': _to_youtube_video_link(url)
    if media_type == media.MediaTypeEnum.YOUTUBE_VIDEO
    else url,
    'media_preview': _to_youtube_preview_link(url)
    if media_type == media.MediaTypeEnum.YOUTUBE_VIDEO
    else url,
  }


def _to_youtube_preview_link(video_id: str) -> str:
  return f'https://img.youtube.com/vi/{video_id}/0.jpg'


def _to_youtube_video_link(video_id: str) -> str:
  return f'https://www.youtube.com/watch?v={video_id}'
