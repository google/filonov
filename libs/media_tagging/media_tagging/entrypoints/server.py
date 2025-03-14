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
import uvicorn
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

from media_tagging import media_tagging_service, repositories


class MediaTaggingSettings(BaseSettings):
  """Specifies environmental variables for media-tagger.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    media_tagging_db_url: Connection string to DB with tagging results.
  """

  media_tagging_db_url: str | None = None


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


@router.post('/tag')
async def tag(
  request: media_tagging_service.MediaTaggingRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> dict[str, str]:
  """Performs media tagging.

  Args:
    request: Post request for media tagging.
    dependencies: Common dependencies used by endpoint.

  Returns:
    Json results of tagging.
  """
  tagging_results = dependencies.tagging_service.tag_media(request)
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(tagging_results)
  )


@router.post('/describe')
async def describe(
  request: media_tagging_service.MediaTaggingRequest,
  dependencies: Annotated[Dependencies, fastapi.Depends(Dependencies)],
) -> dict[str, str]:
  """Performs media tagging.

  Args:
    request: Post request for media tagging.
    dependencies: Common dependencies used by endpoint.

  Returns:
    Json results of tagging.
  """
  tagging_results = dependencies.tagging_service.describe_media(request)
  return fastapi.responses.JSONResponse(
    content=fastapi.encoders.jsonable_encoder(tagging_results)
  )


if __name__ == '__main__':
  app = fastapi.FastAPI()
  app.include_router(router)
  uvicorn.run(app)
