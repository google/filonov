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
from media_similarity import idf_context


def test_calculate_idf_context_returns_correct_context(
  media_1, media_2, media_3
):
  calculated_idf_context = idf_context.calculate_idf_context(
    [media_1, media_2, media_3]
  )
  assert 'tag1' in calculated_idf_context
