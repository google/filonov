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
import pytest
from media_fetching import MediaFetchingService, exceptions
from media_fetching.sources import dbm, file, googleads, models, sql, youtube


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
      ('dbm', dbm.Fetcher),
      (models.InputSource.file, file.Fetcher),
      (models.InputSource.googleads, googleads.Fetcher),
      (models.InputSource.youtube, youtube.Fetcher),
      (models.InputSource.sqldb, sql.SqlAlchemyQueryFetcher),
      (models.InputSource.bq, sql.BigQueryFetcher),
      (models.InputSource.dbm, dbm.Fetcher),
    ],
  )
  def test_init_from_alias_returns_correct_source_class(
    self, alias, source_class
  ):
    service = MediaFetchingService.from_source_alias(alias)
    assert isinstance(service.fetcher, source_class)

  def test_fetch_dbm_correctly_enriches_report_with_brand_lift_data(
    self, mocker
  ):
    fake_report = garf_core.GarfReport(
      results=[
        ['2025/01/01', 1, '1234567890', 'test_video', 1],
      ],
      column_names=['date', 'ad_group_id', 'media_url', 'media_name', 'clicks'],
    )
    mocker.patch(
      'media_fetching.sources.dbm.Fetcher.fetch_media_data',
      return_value=fake_report,
    )
    fake_report = garf_core.GarfReport(
      results=[
        [1, 'CONSIDERATION', 100],
        [2, 'AWARENESS', 1000],
      ],
      column_names=[
        'ad_group_id',
        'brand_lift_type',
        'brand_lift_absolute_brand_lift',
      ],
    )
    mocker.patch(
      'garf_bid_manager.report_fetcher.BidManagerApiReportFetcher.fetch',
      return_value=fake_report,
    )
    service = MediaFetchingService.from_source_alias('dbm')

    request = dbm.BidManagerFetchingParameters(
      advertiser='1234567890', metrics='clicks', extra_info=['dbm.brand_lift']
    )
    result = service.fetch(request, extra_parameters=request.model_dump())
    expected_report = garf_core.GarfReport(
      results=[
        ['2025/01/01', 1, '1234567890', 'test_video', 1, 'CONSIDERATION', 100],
      ],
      column_names=[
        'date',
        'ad_group_id',
        'media_url',
        'media_name',
        'clicks',
        'brand_lift_type',
        'brand_lift_absolute_brand_lift',
      ],
    )
    assert result == expected_report
