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
import logging
import operator
from collections.abc import Mapping, Sequence
from typing import Literal, TypeAlias

import gaarf
import numpy as np
from filonov import exceptions
from media_tagging import media

MetricInfo: TypeAlias = dict[str, int | float]
Info: TypeAlias = dict[str, int | float | str | list[str]]
SupportedMediaTypes = Literal['IMAGE', 'VIDEO', 'YOUTUBE_VIDEO']


class FilonovInputError(exceptions.FilonovError):
  """Input specific exception."""


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


def convert_gaarf_report_to_media_info(
  performance: gaarf.GaarfReport,
  media_type: media.MediaTypeEnum,
  metric_columns: Sequence[str] | None = None,
  segment_columns: Sequence[str] | None = None,
  with_size_base: str | None = None,
) -> dict[str, MediaInfo]:
  """Convert report to MediaInfo mappings."""
  if with_size_base and with_size_base not in performance.column_names:
    logging.warning('Failed to set MediaInfo size to %s', with_size_base)
    with_size_base = None
  if with_size_base:
    try:
      float(performance[0][with_size_base])
    except TypeError:
      logging.warning('MediaInfo size attribute should be numeric')
    with_size_base = None

  performance = performance.to_dict(key_column='media_url')
  results = {}
  media_size_column = 'file_size' if media_type == 'IMAGE' else 'video_duration'
  common_info_columns = ['orientation', media_size_column]
  metric_columns = metric_columns or []
  for media_url, values in performance.items():
    info = build_info(values, list(metric_columns) + common_info_columns)
    segments = build_info(values, segment_columns) if segment_columns else {}
    if values[0].get('date'):
      series = {
        entry.get('date'): build_info(entry, metric_columns) for entry in values
      }
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


def build_info(data: Info, metric_names: Sequence[str]) -> Info:
  """Extracts and aggregated data for specified metrics."""
  return {
    metric: _aggregate_nested_metric(data, metric) for metric in metric_names
  }


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
