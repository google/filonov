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

"""Defines common operations for reading and building prompts."""

import pathlib
from typing import Literal

from media_tagging.taggers import base


def get_invocation_parameters(
  media_type: str,
  tagging_options: base.TaggingOptions,
) -> dict[str, str | int]:
  """Prepares necessary parameters for LLM prompt.

  Args:
    media_type: Type of media.
    tagging_options: Parameters to refine the tagging results.
    image_data: Optional base64 encoded image.

  Returns:
    Necessary parameters to be invoke by the chain.
  """
  parameters = {
    'media_type': media_type,
  }
  if n_tags := tagging_options.n_tags:
    parameters['n_tags'] = n_tags
  if tags := tagging_options.tags:
    parameters['tags'] = 'Find only the following tags: ' + ', '.join(tags)
  else:
    parameters['tags'] = ''
  return parameters


def read_prompt_content(output_type: Literal['tag', 'description']) -> str:
  """Reads content of a file with prompts based on the output type."""
  prompt_location = (
    pathlib.Path(__file__).resolve().parent / 'prompts' / output_type
  )
  with pathlib.Path.open(
    prompt_location.with_suffix('.txt'),
    'r',
    encoding='utf-8',
  ) as f:
    template = f.readlines()
  return ' '.join(template)
