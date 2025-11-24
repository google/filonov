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
"""Module for faking media tagging results."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from typing_extensions import override

from media_tagging import media
from media_tagging.taggers import base
from media_tagging.taggers.fake import tagging_strategies as ts


class FakeTaggerError(base.TaggerError):
  """Fake specific exception."""


class FakeTagger(base.BaseTagger):
  """Tags media via Fake."""

  alias = 'fake'

  @override
  def __init__(
    self,
    n_tags: int = 10,
    **kwargs: str,
  ) -> None:
    """Initializes FakeTagger.

    Args:
      n_tags: Number of tags to generate.
    """
    self.n_tags = n_tags
    super().__init__()

  @override
  def create_tagging_strategy(
    self, media_type: media.MediaTypeEnum
  ) -> base.TaggingStrategy:
    return ts.FakeTaggingStrategy(n_tags=self.n_tags)
