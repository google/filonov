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
import pydantic

from media_tagging import media_tagging_service, repositories

app = fastapi.FastAPI()

tagging_service = media_tagging_service.MediaTaggingService(
  repositories.SqlAlchemyTaggingResultsRepository(
    os.getenv('MEDIA_TAGGING_DB_URL')
  )
)


class MediaTaggingPostRequest(pydantic.BaseModel):
  """Specifies structure of request for tagging media.

  Attributes:
    tagger_type: Type of tagger.
    media_url: Local or remote URL of media.
  """

  media_paths: list[str]
  tagger_type: str
  tagging_parameters: dict[str, int | list[str]] | None = None


@app.post('/tag')
async def tag(
  request: MediaTaggingPostRequest,
) -> dict[str, str]:
  """Performs media tagging.

  Args:
    request: Post request for media tagging.

  Returns:
    Json results of tagging.
  """
  tagging_results = tagging_service.tag_media(
    tagger_type=request.tagger_type,
    media_paths=request.media_paths,
    tagging_parameters=request.tagging_parameters,
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(tagging_results)
  )
