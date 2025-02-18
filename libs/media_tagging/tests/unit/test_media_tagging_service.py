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

from media_tagging import media_tagging_service, repositories, tagging_result


def test_tag_media_saves_tagging_results_to_repository(mocker, tmp_path):
  expected_result = tagging_result.TaggingResult(
    identifier='test',
    type='image',
    content=tagging_result.Description(text='Test description.'),
  )
  mocker.patch(
    'media_tagging.taggers.google_cloud.tagger.GoogleCloudTagger.tag',
    return_value=expected_result,
  )
  persist_repository_path = f'sqlite:///{tmp_path}.db'
  persist_repository = repositories.SqlAlchemyTaggingResultsRepository(
    persist_repository_path
  )
  tagging_service = media_tagging_service.MediaTaggingService(
    repositories.SqlAlchemyTaggingResultsRepository(persist_repository_path)
  )
  test_tagging_result = tagging_service.tag_media(
    tagger_type='google-cloud',
    media_type='IMAGE',
    media_paths=['test'],
    parallel_threshold=0,
  )

  assert test_tagging_result == [expected_result]
  assert persist_repository.list() == [expected_result]
