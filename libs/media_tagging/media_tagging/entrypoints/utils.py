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

"""Defines helper functions for media tagging entrypoints."""

import functools
import logging
import os

import pandas as pd
import pydantic
import smart_open

from media_tagging import exceptions


def parse_typer_arguments(
  arguments: list[str] | None,
) -> tuple[list[str], list[str]]:
  if not arguments:
    return [], []
  found_arguments = []
  parameters = []
  for argument in arguments:
    if argument.startswith('--'):
      parameters.append(argument)
    else:
      found_arguments.append(argument)
  return found_arguments, parameters


def log_shutdown(func):
  @functools.wraps(func)
  def fn(*args, **kwargs):
    func(*args, **kwargs)
    logging.shutdown()

  return fn
