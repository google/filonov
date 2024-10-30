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
"""Provides HTTP endpoint for media tagging."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import os

import fastapi
from typing_extensions import TypedDict

from media_tagging import repository, tagger
from media_tagging.tagger import base as base_tagger

taggers: dict[str, base_tagger.BaseTagger] = {}
app = fastapi.FastAPI()

if db_url := os.getenv('MEDIA_TAGGING_DB_URL'):
  persist_repository = repository.SqlAlchemyTaggingResultsRepository(db_url)
  persist_repository.initialize()
else:
  persist_repository = None


class MediaPostRequest(TypedDict):
  """Specifies structure of request for tagging media.

  Attributes:
    tagger_type: Type of tagger.
    media_url: Local or remote URL of media.
  """

  media_url: str
  tagger_type: str
  tagging_parameters: dict[str, int | list[str]]


@app.post('/tagger/llm')
async def tag_with_llm(
  data: MediaPostRequest = fastapi.Body(embed=True),
) -> dict[str, str]:
  """Performs media tagging via LLMs.

  Args:
    data: Post request for media tagging.

  Returns:
    Json results of tagging.
  """
  return process_post_request(data)


@app.post('/tagger/api')
async def tag_with_api(
  data: MediaPostRequest = fastapi.Body(embed=True),
) -> dict[str, str]:
  """Performs media tagging via Google Cloud APIs.

  Args:
    data: Post request for media tagging.

  Returns:
    Json results of tagging.
  """
  return process_post_request(data)


def process_post_request(
  data: MediaPostRequest,
) -> fastapi.responses.JSONResponse:
  """Helper method for performing tagging.

  Args:
    data: Post request for media tagging.

  Returns:
    Json results of tagging.
  """
  tagger_type = data.get('tagger_type')
  if not (concrete_tagger := taggers.get(tagger_type)):
    concrete_tagger = tagger.create_tagger(tagger_type)
    taggers[tagger_type] = concrete_tagger
  if media_url := data.get('media_url'):
    tagging_results = concrete_tagger.tag_media(
      media_paths=[media_url],
      tagging_parameters=data.get('tagging_parameters'),
      persist_repository=persist_repository,
    )
    return fastapi.responses.JSONResponse(
      content=fastapi.encoders.jsonable_encoder(tagging_results[0].dict())
    )
  raise ValueError('No path to media is provided.')
