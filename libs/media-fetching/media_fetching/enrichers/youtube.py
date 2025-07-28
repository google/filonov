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

"""YouTube specific enrichers."""

import garf_youtube_data_api
from garf_core import report

from media_fetching import exceptions
from media_fetching.enrichers import extra_info


class YouTubeEnricherError(exceptions.MediaFetchingError):
  """Google Ads specific exceptions for enricher."""


class YouTubeEnricher:
  """Injects YouTube specific information into existing reports."""

  @property
  def fetcher(self):
    """Initialized Report fetcher from YouTube Data API."""
    return garf_youtube_data_api.YouTubeDataApiReportFetcher()

  def language(
    self, performance: report.GarfReport, **kwargs: str
  ) -> extra_info.ExtraInfo:
    """Gets either visual or spoken language of YouTube video."""
    video_ids = performance['media_url'].to_list(
      row_type='scalar', distinct=True
    )
    language_query = """
    SELECT
      id,
      snippet.defaultLanguage AS language,
      snippet.defaultAudioLanguage AS audio_language
    FROM videos
    """
    languages = self.fetcher.fetch(
      language_query,
      id=video_ids,
    )
    return extra_info.ExtraInfo(
      info={
        r.id: {'language': r.language or r.audio_language or 'Unknown'}
        for r in languages
      },
    )
