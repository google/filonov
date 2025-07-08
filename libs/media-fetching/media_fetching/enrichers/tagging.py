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

"""Media tagging specific enrichers."""

from typing import Literal

import media_tagging
from garf_core import report

from media_fetching.enrichers import extra_info


class MediaTaggingEnricher:
  """Uses media tagging library to add extra information into reports."""

  def __init__(self, db_uri: str | None = None) -> None:
    """Initializes MediaTaggingEnricher."""
    self.tagging_service = media_tagging.MediaTaggingService(
      media_tagging.repositories.SqlAlchemyTaggingResultsRepository(db_uri)
    )

  def language(
    self,
    performance: report.GarfReport,
    media_type: Literal['IMAGE', 'YOUTUBE_VIDEO'],
  ) -> extra_info.ExtraInfo:
    """Infers languages of each media."""
    media_urls = performance['media_url'].to_list(
      row_type='scalar', distinct=True
    )
    media_path_mapping = {
      media_tagging.media.convert_path_to_media_name(media_url): media_url
      for media_url in media_urls
    }
    languages = self.tagging_service.describe_media(
      media_tagging.MediaTaggingRequest(
        tagger_type='gemini',
        media_type=media_type,
        media_paths=media_urls,
        tagging_options={
          'custom_prompt': (
            f'What is the language of this {media_type}? '
            'Provide only a lowercase name of the language '
            '(english, spanish, japanese).'
          )
        },
      )
    )
    return extra_info.ExtraInfo(
      info={
        media_path_mapping.get(r.identifier): {'language': r.content.text}
        for r in languages.results
      },
    )
