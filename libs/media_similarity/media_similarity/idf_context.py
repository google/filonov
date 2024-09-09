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
"""Defines Inverse-Document Frequency context."""

from collections import UserDict, defaultdict
from collections.abc import Sequence

import numpy as np
from media_tagging import tagging_result


class IdfContext(UserDict):
  """Stores Inverse-Document Frequency (IDF) for each key."""

  def __getitem__(self, key) -> float:
    """Returns IDF value for a key."""
    return super().__getitem__(key).__getitem__('idf')

  def __missing__(self, key: str) -> dict[str, float]:
    """Returns IDF with value 1.0."""
    return {'idf': 1.0}


def calculate_idf_context(
  tagging_results: Sequence[tagging_result.TaggingResult],
) -> IdfContext:
  """Calculates Inverse-Document Frequency (IDF) for each tag.

  Args:
    tagging_results: Results of tagging for multiple media.

  Returns:
    Mapping between each tag and its IDF value.
  """
  idf_context: dict[str, dict[str, float]] = defaultdict(
    lambda: defaultdict(float)
  )
  for result in tagging_results:
    for tag in result.content:
      idf_context[tag.name]['total_media'] += 1
  for tag in idf_context:
    idf_context[tag]['idf'] = np.log(
      len(tagging_results) / idf_context[tag]['total_media']
    )
  return IdfContext(idf_context)
