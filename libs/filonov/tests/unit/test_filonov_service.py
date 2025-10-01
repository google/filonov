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

import garf_core
import media_fetching
import media_similarity
import media_tagging
import pytest
from filonov import exceptions, filonov_service

DATA = garf_core.GarfReport(
  results=[
    ['example.com', 'example', 1],
  ],
  column_names=['media_url', 'media_name', 'clicks'],
)


class TestCreativeMapGenerateRequest:
  @pytest.mark.parametrize(
    'tagger_parameters',
    [{'custom_prompt': 'test prompt'}, {}],
  )
  def test_model_post_init_creates_correct_tagger_parameters(
    self, tagger_parameters
  ):
    expected_parameters = dict(tagger_parameters)
    request = filonov_service.CreativeMapGenerateRequest(
      source='fake', tagger_parameters=tagger_parameters
    )
    expected_parameters.update({'n_tags': 100})
    assert request.tagger_parameters == expected_parameters


class TestFilonovService:
  @pytest.fixture
  def db_uri(self, tmp_path):
    db_path = tmp_path / 'test.db'
    return f'sqlite:///{str(db_path)}'

  def test_generate_creative_maps_returns_filonov_error_when_no_tagger_or_repo(
    self,
  ):
    service = filonov_service.FilonovService()
    with pytest.raises(
      exceptions.FilonovError,
      match='Failed to get tagging results from DB. MediaTaggingService missing',
    ):
      service.generate_creative_map(
        request=filonov_service.CreativeMapGenerateRequest(
          source='fake', media_type='IMAGE'
        ),
      )

  def test_generate_creative_maps_returns_filonov_error_when_no_media_data(
    self,
  ):
    fake_fetcher = media_fetching.sources.fake.FakeFetcher(
      garf_core.GarfReport(results=[], column_names=['media_url'])
    )
    fake_fetching_service = media_fetching.MediaFetchingService(
      source_fetcher=fake_fetcher
    )
    service = filonov_service.FilonovService(
      fetching_service=fake_fetching_service,
      tagging_service=media_tagging.MediaTaggingService(
        media_tagging.repositories.SqlAlchemyTaggingResultsRepository()
      ),
    )
    with pytest.raises(
      exceptions.FilonovError, match='No performance data found for the context'
    ):
      service.generate_creative_map(
        request=filonov_service.CreativeMapGenerateRequest(
          source='fake', media_type='IMAGE'
        ),
      )

  def test_generate_creative_maps_returns_generated_map(self, db_uri):
    fake_fetcher = media_fetching.sources.fake.FakeFetcher(DATA)
    fake_fetching_service = media_fetching.MediaFetchingService(
      source_fetcher=fake_fetcher
    )
    service = filonov_service.FilonovService(
      fetching_service=fake_fetching_service,
      tagging_service=media_tagging.MediaTaggingService(
        media_tagging.repositories.SqlAlchemyTaggingResultsRepository(db_uri)
      ),
      similarity_service=(
        media_similarity.MediaSimilarityService.from_connection_string(db_uri)
      ),
    )
    generated_map = service.generate_creative_map(
      request=filonov_service.CreativeMapGenerateRequest(
        source='fake', media_type='IMAGE'
      ),
    )
    assert generated_map
