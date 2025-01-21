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

import garf_youtube_data_api
from filonov.inputs import interfaces
from media_tagging import media


class ExtraInfoFetcher:
  """Extracts additional information from YouTube to build CreativeMap."""

  def __init__(self, channel: str) -> None:
    """Initializes ExtraInfoFetcher."""
    self.channel = channel

  def generate_extra_info(self) -> dict[str, interfaces.MediaInfo]:
    """Extracts data from YouTube Data API and converts to MediaInfo objects."""
    youtube_api_fetcher = garf_youtube_data_api.YouTubeDataApiReportFetcher()
    channel_uploads_playlist_query = """
    SELECT
      contentDetails.relatedPlaylists.uploads AS uploads_playlist
    FROM channels
    """
    videos_playlist = youtube_api_fetcher.fetch(
      channel_uploads_playlist_query,
      id=[self.channel],
    )

    channel_videos_query = """
    SELECT
      contentDetails.videoId AS video_id
    FROM playlistItems
    """
    videos = youtube_api_fetcher.fetch(
      channel_videos_query, playlistId=videos_playlist[0], maxResults=50
    ).to_list(flatten=True, distinct=True)

    video_performance_query = """
    SELECT
      id AS media_url,
      snippet.title AS media_name,
      contentDetails.duration AS media_size,
      statistics.viewCount AS views,
      statistics.likeCount AS likes
    FROM videos
    """
    video_performance = youtube_api_fetcher.fetch(
      video_performance_query, id=videos
    )
    for row in video_performance:
      row['views'] = int(row.views)
      row['likes'] = int(row.likes)
    video_performance = video_performance.to_dict(key_column='media_url')
    results = {}
    core_metrics = ('likes', 'views')

    for media_url, values in video_performance.items():
      info = interfaces.build_info(values, core_metrics)
      info.update(
        {
          'orientation': values[0].get('orientation', 'null'),
          'media_size': values[0].get('media_size', 'null'),
        }
      )
      results[media.convert_path_to_media_name(media_url)] = (
        interfaces.MediaInfo(
          **interfaces.create_node_links(media_url, 'youtube_video'),
          media_name=values[0].get('media_name').replace("'", ''),
          info=info,
          series={},
        )
      )
    return results
