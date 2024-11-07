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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-module-docstring, missing-class-docstring, missing-function-docstring

import pytest
from media_tagging import tagging_result
from media_tagging.taggers import base


class FakeTagger(base.BaseTagger):
  def tag(
    self, image_name: str = 'test', image_bytes: bytes | None = None
  ) -> tagging_result.TaggingResult:
    del image_bytes
    return tagging_result.TaggingResult(
      identifier=image_name,
      type='image',
      content=(tagging_result.Tag(name='test', score=0.0),),
    )


@pytest.fixture
def fake_tagger():
  return FakeTagger()
