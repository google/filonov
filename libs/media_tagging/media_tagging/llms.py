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
"""Module for defining various LLMs."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
from __future__ import annotations

import os

import langchain_google_genai as genai
from langchain_core import language_models

_GEMINI_SAFETY_SETTINGS: dict[genai.HarmCategory, genai.HarmBlockThreshold] = {
  genai.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: (
    genai.HarmBlockThreshold.BLOCK_NONE
  ),
  genai.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: (
    genai.HarmBlockThreshold.BLOCK_NONE
  ),
  genai.HarmCategory.HARM_CATEGORY_HARASSMENT: (
    genai.HarmBlockThreshold.BLOCK_NONE
  ),
}


def create_llm(
  llm_type: str, llm_parameters: dict[str, str] | None = None
) -> language_models.BaseLanguageModel:
  """Creates LLM based on type and parameters.

  Args:
    llm_type: Type of LLM to instantiate.
    llm_parameters: Various parameters to instantiate LLM.

  Returns:
    Initialized LLM.

  Raises:
    InvalidLLMTypeError: When incorrect LLM type is specified.
  """
  mapping = {
    'gemini': genai.ChatGoogleGenerativeAI,
  }
  if llm := mapping.get(llm_type):
    if not llm_parameters:
      llm_parameters = {}
    if llm_type == 'gemini':
      llm_parameters.update(
        {
          'safety_settings': _GEMINI_SAFETY_SETTINGS,
          'google_api_key': os.environ.get('GOOGLE_API_KEY'),
        }
      )
    return llm(**llm_parameters)
  raise InvalidLLMTypeError(f'Unsupported LLM type: {llm_type}')


class InvalidLLMTypeError(Exception):
  """Error when incorrect LLM type is specified."""
