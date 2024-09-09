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
import pytest
from media_tagging import tagging_result


@pytest.fixture
def media_1():
  return tagging_result.TaggingResult(
    identifier='media_1',
    type='image',
    content=(
      tagging_result.Tag(name='tag1', score=1.0),
      tagging_result.Tag(name='tag2', score=1.0),
    ),
  )


@pytest.fixture
def media_2():
  return tagging_result.TaggingResult(
    identifier='media_2',
    type='image',
    content=(
      tagging_result.Tag(name='tag1', score=0.5),
      tagging_result.Tag(name='tag3', score=1.0),
    ),
  )


@pytest.fixture
def media_3():
  return tagging_result.TaggingResult(
    identifier='media_3',
    type='image',
    content=(
      tagging_result.Tag(name='tag3', score=1.0),
      tagging_result.Tag(name='tag4', score=1.0),
    ),
  )
