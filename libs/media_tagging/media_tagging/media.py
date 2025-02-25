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
  YOUTUBE_VIDEO = 3

  @classmethod
  def options(cls) -> list[str]:
    return [option for option in cls.__members__ if option != 'UNKNOWN']


class Medium:
  """Represents a single Medium."""

  def __init__(
    self,
    media_path: str,
    media_type: MediaTypeEnum = MediaTypeEnum.UNKNOWN,
    media_name: str = '',
  ) -> None:
    """Initializes Medium."""
    self._media_path = media_path
    self._media_type = media_type
    self._name = media_name
    self._content: bytes = bytes()

  @property
  def media_path(self) -> str:
    """Normalized path to media.

    Converts YouTube Shorts links to YouTube video link.
    """
    if self.type == MediaTypeEnum.YOUTUBE_VIDEO:
      return f'https://www.youtube.com/watch?v={self.name}'
    return self._media_path

  @property
  def name(self) -> str:
    """Normalized name."""
    if self._name:
      return self._name
    self._name = convert_path_to_media_name(self._media_path, self.type)
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
      if self.type in (MediaTypeEnum.YOUTUBE_VIDEO, MediaTypeEnum.UNKNOWN):
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


class InvalidMediaTypeError(Exception):
  """Raised when media type is invalid."""

  def __init__(self, media_type: str) -> None:
    """Initializes InvalidMediaTypeError."""
    super().__init__(
      f'Incorrect media_type: {media_type}, '
      f'supported type are: {MediaTypeEnum.options()}'
    )


def convert_path_to_media_name(
  media_path: str, media_type: MediaTypeEnum | str = MediaTypeEnum.UNKNOWN
) -> str:
  """Extracts file name without extension."""
  if isinstance(media_type, str):
    media_type = MediaTypeEnum[media_type.upper()]
  if media_type == MediaTypeEnum.YOUTUBE_VIDEO:
    return _convert_youtube_link_to_id(media_path)
  base_name = media_path.split('/')[-1]
  return base_name.split('.')[0]


def _convert_youtube_link_to_id(youtube_video_link: str) -> str:
  """Extracts YouTube video id from the link.

  Args:
    youtube_video_link: Link to video on YouTube.

  Returns:
    YouTube video_id.

  Raises:
    InvalidMediaPathError: If incorrect link is supplied.
  """
  video_id_length = 11
  if 'shorts' in youtube_video_link:
    youtube_link_parts = youtube_video_link.split('shorts/')
  elif 'watch?v=' in youtube_video_link:
    youtube_link_parts = youtube_video_link.split('?v=')
  elif 'youtu.be' in youtube_video_link:
    youtube_link_parts = youtube_video_link.split('youtu.be/')
  else:
    youtube_link_parts = youtube_video_link.split('/')
  if (
    len(youtube_video_id := youtube_link_parts[-1][:video_id_length])
    != video_id_length
  ):
    raise InvalidMediaPathError(
      'Provide URL of YouTube Video in https://youtube.com/watch?v=<VIDEO_ID> '
      'or https://youtube.com/shorts/<VIDEO_ID> format'
    )
  return youtube_video_id
