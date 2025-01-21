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
"""Defines interfaces for input data."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import dataclasses
import operator
from collections.abc import Mapping, Sequence
from typing import TypeAlias

MetricInfo: TypeAlias = dict[str, int | float]
Info: TypeAlias = dict[str, int | float | str | list[str]]


@dataclasses.dataclass
class MediaInfo:
  """Contains extra information on a given medium."""

  media_path: str
  media_name: str
  info: Info
  series: dict[str, MetricInfo]
  media_preview: str | None = None
  size: float | None = None
  segments: dict[str, Info] | None = None

  def __post_init__(self) -> None:  # noqa: D105
    if not self.media_preview:
      self.media_preview = self.media_path
    self.info = dict(self.info)


def build_info(data: Info, metric_names: Sequence[str]) -> Info:
  """Extracts and aggregated data for specified metrics."""
  return {
    metric: _aggregate_nested_metric(data, metric) for metric in metric_names
  }


def _aggregate_nested_metric(
  data: Info | Sequence[Info],
  metric_name: str,
) -> float | int | str | list[str]:
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
  res = list(map(get_metric_getter, data))
  try:
    return sum(res)
  except TypeError:
    return sorted(set(res))


def create_node_links(url: str, media_type: str) -> dict[str, str]:
  return {
    'media_path': _to_youtube_video_link(url)
    if media_type.lower() == 'youtube_video'
    else url,
    'media_preview': _to_youtube_preview_link(url)
    if media_type.lower() == 'youtube_video'
    else url,
  }


def _to_youtube_preview_link(video_id: str) -> str:
  return f'https://img.youtube.com/vi/{video_id}/0.jpg'


def _to_youtube_video_link(video_id: str) -> str:
  return f'https://www.youtube.com/watch?v={video_id}'
