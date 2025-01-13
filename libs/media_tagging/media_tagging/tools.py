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
"""Exposes media tagger as a tool for Langchain agents."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import langchain_core

from media_tagging import repositories, tagger


class MediaTaggingInput(langchain_core.pydantic_v1.BaseModel):
  """Input for media tagging."""

  tagger_type: str = langchain_core.pydantic_v1.Field(
    description='Type of media tagger'
  )
  media_url: str = langchain_core.pydantic_v1.Field(
    description='URL to get media from'
  )


class MediaTaggingResults(langchain_core.tools.BaseTool):
  """Tools that performs media tagging.

  Attributes:
    name: Name of the tool.
    description: Description the tool.
    args_schema: Input model for the tool.
  """

  name: str = 'media_tagger'
  description: str = tagger.MEDIA_TAGGER_DESCRIPTION
  persist_repository: repositories.BaseTaggingResultsRepository = 'sqlite://'
  args_schema: type[langchain_core.pydantic_v1.BaseModel] = MediaTaggingInput

  def _run(
    self,
    tagger_type: str,
    media_url: str,
    tagging_parameters: dict[str, str] | None = None,
  ) -> list[dict[str, str]]:
    """Performs media tagging based on selected tagger.

    Args:
      tagger_type: Type of tagger to use for media tagging.
      media_url: URLs of media to be tagged.
      tagging_parameters: Optional keywords arguments to be sent for tagging.

    Returns:
      Mappings between medium and its tags.
    """
    media_tagger = tagger.create_tagger(tagger_type)
    tagging_results = media_tagger.tag_media(
      media_paths=[media_url],
      tagging_parameters=tagging_parameters,
      persist_repository=self.persist_repository,
    )
    return tagging_results[0].dict()
