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

"""Defined tagging strategies specific to Fake."""

from typing_extensions import override

from media_tagging import media, tagging_result
from media_tagging.taggers import base


class FakeTaggingStrategy(base.TaggingStrategy):
  """Defines set of operations specific to tagging natively via Fake."""

  def __init__(
    self,
    n_tags: int,
  ) -> None:
    """Initializes FakeTaggingStrategy."""
    self.n_tags = n_tags
    super().__init__()

  @override
  def tag(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions,
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    tags = self._fake_tags(tagging_options)
    return tagging_result.TaggingResult(
      identifier=medium.name,
      type=medium.type.name.lower(),
      content=tags,
      hash=medium.identifier,
    )

  @override
  def describe(
    self,
    medium: media.Medium,
    tagging_options: base.TaggingOptions,
    **kwargs: str,
  ) -> tagging_result.TaggingResult:
    return tagging_result.TaggingResult(
      identifier=medium.name,
      type=medium.type.name.lower(),
      content=tagging_result.Description(text=self._fake_description()),
      hash=medium.identifier,
    )

  def _fake_tags(self, tagging_options) -> str:
    return [
      tagging_result.Tag(name=f'fake_{i}', score=1.0)
      for i in range(tagging_options.n_tags or self.n_tags)
    ]

  def _fake_description(self) -> str:
    return 'fake'
