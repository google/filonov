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

"""Defines fetching data from YouTube channel."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import garf_core
import garf_youtube_data_api
import pydantic
from filonov.inputs import interfaces
from media_tagging import media


class YouTubeInputParameters(pydantic.BaseModel):
  """YouTube specific parameters for generating creative map."""

  model_config = pydantic.ConfigDict(extra='ignore')

  channel: str


class ExtraInfoFetcher:
  """Extracts additional information from YouTube to build CreativeMap."""

  def generate_extra_info(
    self,
    fetching_request: YouTubeInputParameters,
    media_type: str = 'YOUTUBE_VIDEO',
    with_size_base: str | None = None,
  ) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from YouTube Data API and converts to MediaInfo objects."""
    if media_type != 'YOUTUBE_VIDEO':
      raise interfaces.FilonovInputError(
        'Only YOUTUBE_VIDEO media type is supported.'
      )
    video_performance = self.fetch_channel_videos(fetching_request)
    for row in video_performance:
      row['views'] = int(row.views)
      row['likes'] = int(row.likes)
    core_metrics = ('likes', 'views')
    return interfaces.convert_gaarf_report_to_media_info(
      performance=video_performance,
      media_type=media.MediaTypeEnum.YOUTUBE_VIDEO,
      metric_columns=core_metrics,
      with_size_base=with_size_base,
    )

  def fetch_channel_videos(
    self,
    fetching_request: YouTubeInputParameters,
  ) -> garf_core.report.GarfReport:
    """Get all public videos from YouTube channel."""
    youtube_api_fetcher = garf_youtube_data_api.YouTubeDataApiReportFetcher()
    channel_uploads_playlist_query = """
    SELECT
      contentDetails.relatedPlaylists.uploads AS uploads_playlist
    FROM channels
    """
    videos_playlist = youtube_api_fetcher.fetch(
      channel_uploads_playlist_query,
      id=[fetching_request.channel],
    )

    channel_videos_query = """
    SELECT
      contentDetails.videoId AS video_id
    FROM playlistItems
    """
    videos = youtube_api_fetcher.fetch(
      channel_videos_query,
      playlistId=videos_playlist.to_list(flatten=True, distinct=True),
      maxResults=50,
    ).to_list(flatten=True, distinct=True)

    video_performance_query = """
    SELECT
      id AS media_url,
      snippet.title AS media_name,
      contentDetails.duration AS video_duration,
      statistics.viewCount AS views,
      statistics.likeCount AS likes
    FROM videos
    """
    return youtube_api_fetcher.fetch(video_performance_query, id=videos)
