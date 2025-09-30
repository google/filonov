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


import garf_core
from media_fetching.sources import fake

DATA = garf_core.GarfReport(
  results=[
    ['example.com', 'example', 1],
  ],
  column_names=['media_url', 'media_name', 'clicks'],
)


class TestFakeFetcher:
  def test_fetch_media_data_returns_data_back(self):
    test_data = fake.FakeFetcher(DATA).fetch_media_data()
    assert test_data == DATA
