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

import media_tagging
import pytest
from filonov import exceptions, filonov_service
from filonov.inputs import interfaces


class TestFilonovService:
  @pytest.fixture
  def service(self):
    return filonov_service.FilonovService(
      tagging_service=media_tagging.MediaTaggingService(
        media_tagging.repositories.SqlAlchemyTaggingResultsRepository()
      ),
      similarity_service=None,
    )

  def test_generate_creative_maps_returns_filonov_error_when_no_media_urls(
    self, service, mocker
  ):
    mocker.patch(
      'filonov.inputs.input_service.MediaInputService.generate_media_info',
      return_value=({}, {}),
    )
    with pytest.raises(
      exceptions.FilonovError, match='No performance data found for the context'
    ):
      service.generate_creative_map(
        source='googleads',
        request=filonov_service.CreativeMapGenerateRequest(source='googleads'),
      )

  def test_generate_creative_maps_returns_filonov_error_when_no_tagging_results(
    self, service, mocker
  ):
    mocker.patch(
      'filonov.inputs.input_service.MediaInputService.generate_media_info',
      return_value=(
        {
          'test_media': interfaces.MediaInfo(
            media_name='test_media',
            media_path='test_image.png',
            info={},
            series={},
          )
        },
        {},
      ),
    )
    mocker.patch(
      'media_tagging.media_tagging_service.MediaTaggingService.tag_media',
      return_value=([]),
    )
    with pytest.raises(
      exceptions.FilonovError,
      match='Failed to perform media tagging for the context',
    ):
      service.generate_creative_map(
        source='googleads',
        request=filonov_service.CreativeMapGenerateRequest(source='googleads'),
      )
