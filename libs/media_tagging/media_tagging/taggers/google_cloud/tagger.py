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
"""Module for performing media tagging via Google APIs.

Media tagging sends API requests to tagging engine (i.e. Google Vision API)
and returns tagging results that can be easily written.
"""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
from __future__ import annotations

import os

from typing_extensions import override

from media_tagging import media
from media_tagging.taggers import base
from media_tagging.taggers.google_cloud import tagging_strategies as ts


class GoogleCloudTagger(base.BaseTagger):
  """Tags media via available Google Cloud APIs."""

  alias = 'google-cloud'

  def __init__(
    self,
    project: str | None = os.getenv('GOOGLE_CLOUD_PROJECT'),
    **kwargs: str,
  ) -> None:
    """Initializes GoogleCloudTagger."""
    if not project:
      raise GoogleCloudTaggerError(
        'Project is not specified, '
        'either expose ENV variable GOOGLE_CLOUD_PROJECT '
        'or specify `project` parameter.'
      )
    self.project = project
    super().__init__()

  @override
  def create_tagging_strategy(
    self, media_type: media.MediaTypeEnum
  ) -> base.TaggingStrategy:
    if media_type == media.MediaTypeEnum.IMAGE:
      return ts.ImageTaggingStrategy(self.project)
    if media_type == media.MediaTypeEnum.VIDEO:
      return ts.VideoTaggingStrategy(self.project)
    raise base.TaggerError(
      f'There are no supported taggers for media type: {media_type.name}'
    )


class GoogleCloudTaggerError(Exception):
  """Google cloud specific exceptions."""
