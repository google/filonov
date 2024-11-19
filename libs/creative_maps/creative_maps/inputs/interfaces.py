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


@dataclasses.dataclass
class MediaInfo:
  """Contains extra information on a given medium."""

  media_path: str
  media_name: str
  info: dict[str, str | int | float]
  series: list[dict[str, dict[str, str | int | float]]]
  media_preview: str | None = None

  def __post_init__(self) -> None:  # noqa: D105
    if not self.media_preview:
      self.media_preview = self.media_path
    self.info = dict(self.info)
