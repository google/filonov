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
import textwrap
from io import BytesIO

import smart_open
from PIL import Image, ImageDraw, ImageFont, ImageOps


def _create_text_image_bytes(
  node_info,
  *,
  format: str = 'PNG',
  font_size: int = 40,
  font_path: str | None = None,
  trim_treshold: int = 100,
  border=1,
):
  text = node_info.media_path[:trim_treshold]
  logging.info('Embedding preview for text %s', text)
  text = '\n'.join(textwrap.wrap(text, width=20))
  dummy_img = Image.new(mode='RGB', size=(1, 1))
  dummy_draw = ImageDraw.Draw(dummy_img)

  font = (
    ImageFont.truetype(font_path, font_size)
    if font_path
    else ImageFont.load_default(size=font_size)
  )

  bbox = dummy_draw.textbbox((0, 0), text, font=font)
  width = bbox[2] - bbox[0] + 10
  height = bbox[3] - bbox[1] + 10

  img = Image.new(mode='RGB', size=(width, height), color='white')
  img = ImageOps.expand(img, border=border, fill=(211, 211, 211))
  draw = ImageDraw.Draw(img)

  draw.multiline_text((5, 5), text, fill='black', font=font)

  byte_stream = BytesIO()
  img.save(byte_stream, format=format)

  image_bytes = byte_stream.getvalue()
  encoded_image = base64.b64encode(image_bytes).decode('utf-8')
  return f'data:image/png;base64,{encoded_image}'


def _embed_preview(node_info) -> str:
  logging.info('Embedding preview for url %s', node_info.media_preview)
  with smart_open.open(node_info.media_preview, 'rb') as f:
    image_preview = f.read()
  encoded_image = base64.b64encode(image_preview).decode('utf-8')
  return f'data:image/png;base64,{encoded_image}'


def get_media_preview_strategy(media_type: str, embed_previews: bool):
  if media_type == 'webpage' and embed_previews:
    from filonov import website_previews

    return website_previews.create_webpage_image_bytes
  if media_type in ('webpage', 'text'):
    return _create_text_image_bytes
  if embed_previews:
    return _embed_preview
  return None
