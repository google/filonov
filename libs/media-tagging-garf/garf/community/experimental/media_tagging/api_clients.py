# Copyright 2026 Google LLC
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

import logging
import urllib.parse

import requests
from garf.community.experimental.media_tagging import query_editor
from garf.core import api_clients

from media_tagging import MediaTaggingRequest, MediaTaggingService, repositories

logging.getLogger('media-tagger').setLevel(logging.WARNING)


class MediaTaggingApiClient(api_clients.RestApiClient):
  """Client to work with media tagger.

  MediaTaggingApiClient work work local and remote instances of MediaTagging.

  Attributes:
    endpoint: HTTP endpoint when media tagger is running.
    db_uri: Connection string to DB where media tagger stores tagging results.
  """

  def __init__(
    self,
    endpoint: str | None = None,
    db_uri: str | None = None,
    tagger_type: str = 'gemini',
    schema=None,
    custom_prompt=None,
    **kwargs: str,
  ):
    self.endpoint = endpoint
    self.db_uri = db_uri
    self.tagger_type = tagger_type
    self.schema = schema
    self.custom_prompt = custom_prompt
    self.kwargs = kwargs

  def get_response(
    self, request: query_editor.MediaTaggingApiQuery, **kwargs: str
  ) -> api_clients.GarfApiResponse:
    tagging_request = MediaTaggingRequest(**request.filters)
    if self.endpoint:
      resource = 'describe' if request.resource_name == 'description' else 'tag'
      url = urllib.parse.urljoin(self.endpoint, f'/media_tagging/{resource}')
      response = requests.post(
        url=url,
        json=tagging_request.model_dump(exclude_none=True),
      )
      return api_clients.GarfApiResponse(results=response.json().get('results'))
    service = MediaTaggingService(
      repositories.SqlAlchemyTaggingResultsRepository(self.db_uri)
    )
    if request.resource_name == 'description':
      response = service.describe_media(tagging_request)
    else:
      response = service.tag_media(tagging_request)
    results = [result.model_dump() for result in response.results]
    return api_clients.GarfApiResponse(results=results)
