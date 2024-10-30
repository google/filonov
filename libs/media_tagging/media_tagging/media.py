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
"""Combines various attributes of a file in a Medium.

Medium objects have distinct name, type and optionally content (i.e. YouTube
links does not have content).
"""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import enum

import smart_open


class MediaTypeEnum(enum.Enum):
  """Represents type of a Medium."""

  UNKNOWN = 0
  IMAGE = 1
  VIDEO = 2
  YOUTUBE_LINK = 3


class Medium:
  """Represents a single Medium."""

  def __init__(
    self, media_path: str, media_type: MediaTypeEnum = MediaTypeEnum.UNKNOWN
  ) -> None:
    """Initializes Medium."""
    self._media_path = media_path
    self._media_type = media_type
    self._name = ''
    self._content: bytes = bytes()

  @property
  def media_path(self) -> str:
    """Normalized path to media.

    Converts YouTube Shorts links to YouTube video link.
    """
    if '/shorts/' in self._media_path:
      return f'https://www.youtube.com/watch?v={self.name}'
    return self._media_path

  @property
  def name(self) -> str:
    """Normalized name."""
    if self._name:
      return self._name
    self._name = convert_path_to_media_name(self._media_path)
    return self._name

  @property
  def content(self) -> bytes:
    """Content of media as bytes."""
    if self._content:
      return self._content
    try:
      with smart_open.open(self._media_path, 'rb') as f:
        content = f.read()
    except FileNotFoundError as e:
      if self.type in (MediaTypeEnum.YOUTUBE_LINK, MediaTypeEnum.UNKNOWN):
        content = bytes()
      else:
        raise InvalidMediaPathError(
          f'Cannot read media from path {self._media_path}'
        ) from e
    self._content = content
    return content

  @property
  def type(self) -> MediaTypeEnum:
    """Type of medium."""
    return self._media_type


class InvalidMediaPathError(Exception):
  """Raised when media is inaccessible."""


def convert_path_to_media_name(media_path: str) -> str:
  """Extracts file name without extension."""
  if 'youtube' in media_path:
    return _convert_youtube_link_to_name(media_path)
  base_name = media_path.split('/')[-1]
  return base_name.split('.')[0]


def _convert_youtube_link_to_name(youtube_video_link: str) -> str:
  """Extracts YouTube video id from the link.

  Args:
    youtube_video_link: Link to video on YouTube.

  Returns:
    YouTube video_id.

  Raises:
    ValueError: If incorrect link format is supplied.
  """
  if 'watch?v=' in youtube_video_link:
    return youtube_video_link.split('?v=')[1][:11]
  if 'youtu.be' in youtube_video_link:
    return youtube_video_link.split('youtu.be/')[1][:11]
  if 'youtube.com/shorts' in youtube_video_link:
    return youtube_video_link.split('shorts/')[1][:11]
  raise ValueError(
    'Provide URL of YouTube Video in https://youtube.com/watch?v=<VIDEO_ID> '
    'or https://youtube.com/shorts/<VIDEO_ID> format'
  )
