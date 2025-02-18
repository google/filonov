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

import fastapi
import pydantic
import uvicorn
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

from media_tagging import media_tagging_service, repositories


class MediaTaggingSettings(BaseSettings):
  media_tagging_db_url: str


class Dependencies:
  def __init__(self) -> None:
    """Initializes CommonDependencies."""
    settings = MediaTaggingSettings()
    self.tagging_service = media_tagging_service.MediaTaggingService(
      repositories.SqlAlchemyTaggingResultsRepository(
        settings.media_tagging_db_url
      )
    )


router = fastapi.APIRouter(prefix='/media_tagging')


class MediaTaggingPostRequest(pydantic.BaseModel):
  """Specifies structure of request for tagging media.

  Attributes:
    media_paths: Identifiers or media to cluster (file names or links).
    media_type: Type of media found in media_paths.
    tagger_type: Type of tagger.
    tagging_parameters: Parameters to fine-tune tagging.
  """

  media_paths: list[str]
  tagger_type: str
  media_type: str
  tagging_parameters: dict[str, int | list[str]] | None = None


@router.post('/tag')
async def tag(
  request: MediaTaggingPostRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> dict[str, str]:
  """Performs media tagging.

  Args:
    request: Post request for media tagging.
    dependencies: Common dependencies used by endpoint.

  Returns:
    Json results of tagging.
  """
  tagging_results = dependencies.tagging_service.tag_media(
    tagger_type=request.tagger_type,
    media_type=request.media_type,
    media_paths=request.media_paths,
    tagging_parameters=request.tagging_parameters,
  )
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(tagging_results)
  )


if __name__ == '__main__':
  app = fastapi.FastAPI()
  app.include_router(router)
  uvicorn.run(app)
