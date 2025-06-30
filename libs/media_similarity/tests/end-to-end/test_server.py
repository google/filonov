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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring, missing-function-docstring

import os

import dotenv
import fastapi
import media_similarity
from fastapi import testclient
from media_similarity.entrypoints.server import router

app = fastapi.FastAPI()
app.include_router(router)
client = testclient.TestClient(app)

dotenv.load_dotenv()
MEDIA_IDENTIFIER_1 = os.getenv('FILONOV_MEDIA_IDENTIFIER_1')
MEDIA_IDENTIFIER_2 = os.getenv('FILONOV_MEDIA_IDENTIFIER_2')
MEDIA_IDENTIFIER_3 = os.getenv('FILONOV_MEDIA_IDENTIFIER_3')


class TestMediaSimilarity:
  def test_cluster(self):
    request = media_similarity.MediaClusteringRequest(
      tagger_type='gemini',
      media_type='IMAGE',
      media_paths=[
        MEDIA_IDENTIFIER_1,
        MEDIA_IDENTIFIER_2,
        MEDIA_IDENTIFIER_3,
      ],
    )
    response = client.post(
      '/media_similarity/cluster', json=request.model_dump()
    )
    assert response.status_code == fastapi.status.HTTP_200_OK

  def test_search(self):
    response = client.get(
      '/media_similarity/search',
      params={
        'seed_media_identifiers': MEDIA_IDENTIFIER_1,
        'media_type': 'IMAGE',
        'n_results': 1,
      },
    )
    assert response.status_code == fastapi.status.HTTP_200_OK

  def test_compare(self):
    request = media_similarity.MediaSimilarityComparisonRequest(
      media_type='IMAGE',
      media_paths=[
        MEDIA_IDENTIFIER_1,
        MEDIA_IDENTIFIER_2,
      ],
    )
    response = client.post(
      '/media_similarity/compare', json=request.model_dump()
    )
    assert response.status_code == fastapi.status.HTTP_200_OK
