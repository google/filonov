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
import logging

from filonov import exceptions

try:
  from playwright.sync_api import sync_playwright
except ImportError as e:
  raise exceptions.FilonovError(
    'Missing playwright dependency. '
    'Install it with `pip install filonov[playwright]` '
    'and configure with `playwright install`'
  ) from e


def create_webpage_image_bytes(
  node_info,
  *,
  width: int = 800,
  height: int = 600,
) -> str:
  logging.info('Embedding preview for url %s', node_info.media_path)
  with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': width, 'height': height})
    page.goto(node_info.media_path)
    screenshot = page.screenshot()
    browser.close()
    encoded_image = base64.b64encode(screenshot).decode('utf-8')
    return f'data:image/png;base64,{encoded_image}'
