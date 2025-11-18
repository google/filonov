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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Enricher injects extra data into performance reports."""

from collections.abc import Sequence
from typing import Any

from garf_core import report

from media_fetching import enrichers
from media_fetching.enrichers import extra_info

AVAILABLE_MODULES = {
  'tagging': enrichers.MediaTaggingEnricher,
  'googleads': enrichers.GoogleAdsEnricher,
  'youtube': enrichers.YouTubeEnricher,
  'dbm': enrichers.BidManagerEnricher,
}


def _flatten_dict(params: dict[str, dict[str, Any]]) -> dict[str, Any]:
  flatten_parameters = {}
  for k, v in params.items():
    if not v:
      continue
    if isinstance(v, dict):
      flatten_parameters.update(_flatten_dict(v))
    else:
      flatten_parameters[k] = v
  return flatten_parameters


def prepare_extra_info(
  performance: report.GarfReport,
  modules: Sequence[str],
  params: dict[str, dict[str, str]],
) -> list[extra_info.ExtraInfo]:
  """Builds extra info based on performance report and specified modules.

  Args:
    performance: Report with performance data.
    modules: Modules used to perform enriching.
    params: Parameters to perform enriching.

  Returns:
    All extra info to be injected into the report.
  """
  data = []
  if isinstance(modules, str):
    modules = modules.split(',')
  flattened_parameters = _flatten_dict(params)
  for module in modules:
    enricher_module, method = module.split('.', maxsplit=2)
    if available_module := AVAILABLE_MODULES.get(enricher_module):
      initialized_module = available_module(**params.get(enricher_module, {}))
      info = getattr(initialized_module, method)(
        performance, **flattened_parameters
      )
      data.append(info)
  return data


def enrich(
  performance_report: report.GarfReport,
  extra_data: Sequence[extra_info.ExtraInfo],
) -> None:
  """Adds additional information to existing performance report.

  Args:
    performance_report: Report with performance data.
    extra_data: Information to be injected into performance report.
  """
  for row in performance_report:
    for data in extra_data:
      if not data.info:
        continue
      columns = list(data.info.values())[0].keys()
      for column in columns:
        search_key = row[data.base_key]
        row[column] = data.info.get(search_key, {}).get(column)
