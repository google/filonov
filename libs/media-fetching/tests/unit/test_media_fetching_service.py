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
import pytest
from media_fetching import MediaFetchingService, exceptions
from media_fetching.sources import file, googleads, sql, youtube


class TestMediaFetchingService:
  def test_init_with_missing_source_fetcher_raises_error(self):
    with pytest.raises(
      exceptions.MediaFetchingError, match='Missing source_fetcher parameter'
    ):
      MediaFetchingService()

  def test_init_with_unsupported_source_raises_error(self):
    with pytest.raises(
      exceptions.MediaFetchingError, match='Incorrect source: unknown'
    ):
      MediaFetchingService.from_source_alias('unknown')

  @pytest.mark.parametrize(
    ('alias', 'source_class'),
    [
      ('file', file.Fetcher),
      ('googleads', googleads.Fetcher),
      ('youtube', youtube.Fetcher),
      ('sqldb', sql.SqlAlchemyQueryFetcher),
      ('bq', sql.BigQueryFetcher),
    ],
  )
  def test_init_from_alias_returns_correct_source_class(
    self, alias, source_class
  ):
    service = MediaFetchingService.from_source_alias(alias)
    assert isinstance(service.fetcher, source_class)
