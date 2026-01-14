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
from __future__ import annotations

import base64
import contextlib
import datetime
import hashlib
import io
import logging
import os
import pathlib
from typing import Final

from PIL import Image

from filonov import exceptions

logger = logging.getLogger(__name__)

try:
  from playwright.async_api import async_playwright
except ImportError as e:
  raise exceptions.FilonovError(
    'Missing playwright dependency. '
    'Install it with `pip install filonov[playwright]` '
    'and configure with `playwright install`'
  ) from e

logger = logging.getLogger(__name__)


class CacheFileNotFoundError(exceptions.FilonovError):
  """Exception for not found cached preview."""


DEFAULT_CACHE_LOCATION: Final[str] = os.getenv(
  'FILONOV_PREVIEW_CACHE_LOCATION', str(pathlib.Path.home() / '.filonov/cache/')
)


class Cache:
  """Stores and loads website preview from a cache.

  Attribute:
    location: Folder where cached results are stored.
  """

  def __init__(
    self,
    location: str | None = None,
    ttl_seconds: int = os.getenv('FILONOV_PREVIEW_CACHE_TTL_SECONDS', 3600),
  ) -> None:
    """Stores and loads website preview from a cache.

    Args:
      location: Folder where cached results are stored.
      ttl_seconds: Maximum lifespan of cached objects.
    """
    self.location = pathlib.Path(location or DEFAULT_CACHE_LOCATION)
    self.ttl_seconds = int(ttl_seconds)
    self.media_paths = {}
    self.location.mkdir(parents=True, exist_ok=True)

  @property
  def max_cache_timestamp(self) -> float:
    return (
      datetime.datetime.now() - datetime.timedelta(seconds=self.ttl_seconds)
    ).timestamp()

  def load(
    self,
    media_path: str,
  ) -> str:
    """Loads preview from cache based on media_path.

    Raises:
      CacheFileNotFoundError: If cached report not found.
    """
    path_hash = hashlib.md5(media_path.encode('utf-8')).hexdigest()
    cached_path = self.location / f'{path_hash}.txt'
    if (
      cached_path.exists()
      and cached_path.stat().st_ctime > self.max_cache_timestamp
    ):
      with open(cached_path, 'r', encoding='utf-8') as f:
        data = f.read()
      logger.info('Preview is loaded from cache: %s', str(cached_path))
      return data.strip()
    raise CacheFileNotFoundError

  def save(
    self,
    media_path: str,
    preview: str,
  ) -> None:
    """Saves preview to cache based on media_path."""
    self.location.mkdir(parents=True, exist_ok=True)
    path_hash = hashlib.md5(media_path.encode('utf-8')).hexdigest()
    cached_path = self.location / f'{path_hash}.txt'
    logger.debug('Preview is saved to cache: %s', str(cached_path))
    with open(cached_path, 'w', encoding='utf-8') as f:
      f.write(preview)


cache = Cache()


async def create_webpage_image_bytes(
  node_info,
  *,
  width: int = 1280,
  height: int = 800,
) -> str:
  with contextlib.suppress(CacheFileNotFoundError):
    if encoded_image := cache.load(node_info.media_path):
      return f'data:image/png;base64,{encoded_image}'
  logging.info('Embedding preview for url %s', node_info.media_path)
  async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.set_viewport_size({'width': width, 'height': height})
    await page.goto(node_info.media_path)
    screenshot = await page.screenshot()
    await browser.close()
    resized_screenshot = _resize_image_bytes(screenshot, width=480, height=300)
    encoded_image = base64.b64encode(resized_screenshot).decode('utf-8')
    cache.save(node_info.media_path, encoded_image)
    return f'data:image/png;base64,{encoded_image}'


def _resize_image_bytes(image: bytes, width: int, height: int) -> bytes:
  input_data = io.BytesIO(image)
  with Image.open(input_data) as img:
    resized_image = img.resize((width, height), Image.Resampling.LANCZOS)
    output_data = io.BytesIO()
    resized_image.save(output_data, format=img.format or 'PNG')
    return output_data.getvalue()
