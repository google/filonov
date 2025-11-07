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
import hashlib
import os
import re
import urllib

import pandas as pd
import pydantic
import smart_open

from media_tagging import exceptions

_SUPPORTED_VIDEO_FILE_EXTENSIONS = (
  '.mp4',
  '.avi',
  '.webm',
  '.avi',
  '.flv',
  '.mov',
)


class MediaTypeEnum(str, enum.Enum):
  """Represents type of a Medium."""

  UNKNOWN = 'UNKNOWN'
  IMAGE = 'IMAGE'
  VIDEO = 'VIDEO'
  YOUTUBE_VIDEO = 'YOUTUBE_VIDEO'
  TEXT = 'TEXT'
  WEBPAGE = 'WEBPAGE'

  @classmethod
  def options(cls) -> list[str]:
    return [option for option in cls.__members__ if option != 'UNKNOWN']

  @classmethod
  def options_lowercase(cls) -> list[str]:
    return list(map(str.lower, cls.options()))


class Medium:
  """Represents a single Medium."""

  def __init__(
    self,
    media_path: str | os.PathLike[str],
    media_type: MediaTypeEnum | str = MediaTypeEnum.UNKNOWN,
    media_name: str = '',
    content: bytes = bytes(),
  ) -> None:
    """Initializes Medium."""
    self._media_path = str(media_path)
    self._media_type = (
      media_type
      if isinstance(media_type, MediaTypeEnum)
      else MediaTypeEnum[media_type.upper()]
    )
    self._name = media_name
    self._content: bytes = content

  @property
  def identifier(self) -> str:
    """Represents unique identifier of a medium.

    For YOUTUBE_VIDEO it is video_id which is already unique.
    For IMAGE all links to tpc.googlesyndication.com/simgad are considered
    unique.
    For the rest media type the md5 hash of medium content is taken.
    """
    if self.type == MediaTypeEnum.YOUTUBE_VIDEO or (
      self.type == MediaTypeEnum.IMAGE
      and self._media_path.startswith('https://tpc.googlesyndication.com/')
    ):
      return self.name
    return hashlib.md5(self.content).hexdigest()

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
    if self.type in (MediaTypeEnum.TEXT, MediaTypeEnum.WEBPAGE):
      return self._media_path.encode('utf-8')
    if self._content or (
      self.type == MediaTypeEnum.YOUTUBE_VIDEO
      and not str(self._media_path).endswith(_SUPPORTED_VIDEO_FILE_EXTENSIONS)
    ):
      return self._content
    try:
      with smart_open.open(self._media_path, 'rb') as f:
        content = f.read()
    except FileNotFoundError as e:
      if self.type == MediaTypeEnum.UNKNOWN:
        content = bytes()
      else:
        raise InvalidMediaPathError(
          f'Cannot read media {self.type.name} from path {self._media_path}'
        ) from e
    self._content = content
    return content

  @property
  def type(self) -> MediaTypeEnum:
    """Type of medium."""
    return self._media_type


class InvalidMediaPathError(exceptions.MediaTaggingError):
  """Raised when media is inaccessible."""


class InvalidMediaTypeError(exceptions.MediaTaggingError):
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
  if media_type == MediaTypeEnum.TEXT:
    return media_path
  if media_type == MediaTypeEnum.WEBPAGE:
    return _normalize_website_url(media_path)
  if media_type == MediaTypeEnum.YOUTUBE_VIDEO and not media_path.endswith(
    _SUPPORTED_VIDEO_FILE_EXTENSIONS
  ):
    return _convert_youtube_link_to_id(media_path)
  base_name = str(media_path).split('/')[-1]
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


def _normalize_website_url(media_path: str) -> str:
  if (
    '://' not in media_path and not media_path.startswith('www.')
  ) or media_path.startswith('www.'):
    media_path = f'https://{media_path}'
  elements = urllib.parse.urlsplit(media_path)
  domain = re.sub('^www.', '', elements.netloc)
  if path := elements.path.lstrip('/'):
    clean_path, *rest = path.split('.')
    return f'{domain}/{clean_path}'
  return domain


class InputConfig(pydantic.BaseModel):
  """Parameters for reading media urls from a file.

  Attributes:
    path: Path to a file that contains media urls (either CSV or txt).
    column_name: Column name in a file that contains media_urls.
    skip_rows: Number of rows to skip in a file.
  """

  model_config = pydantic.ConfigDict(extra='ignore')

  path: os.PathLike[str] | str
  column_name: str | None = 'media_url'
  skip_rows: int = 0


def get_media_paths_from_file(input_config: InputConfig) -> set[str]:
  """Reads media urls from a file and returns unique ones.

  Args:
    input_config: Config for reading data from a file.

  Returns:
    Unique media urls.

  Raises:
    MediaTaggingError:
      When specified column with media_urls is not found
      or too many rows skipped.
  """
  if str(input_config.path).endswith('.txt'):
    with smart_open.open(input_config.path, 'r', encoding='utf-8') as f:
      data = f.readlines()
    if skip_rows := input_config.skip_rows:
      if skip_rows < len(data):
        raise exceptions.MediaTaggingError(
          f'Skipping too many rows, data has {len(data)} rows, '
          f'skipping {skip_rows}'
        )
      data = data[skip_rows:]
    return {url.strip() for url in data}

  data = pd.read_csv(
    smart_open.open(input_config.path), skiprows=input_config.skip_rows
  )
  if len(data.columns) == 1:
    column_name = data.columns[0]
  elif (column_name := input_config.column_name) not in data.columns:
    raise exceptions.MediaTaggingError(
      f'Column {column_name} not found in {input_config.path}'
    )
  return set(data[column_name].tolist())
