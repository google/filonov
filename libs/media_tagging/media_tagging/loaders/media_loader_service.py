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

"""Responsible for loading tagging results."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import
import inspect
import os
from importlib.metadata import entry_points
from typing import Literal

from media_tagging import media, repositories
from media_tagging.loaders import base as base_loader


def _get_loaders():
  """Loads all loaders exposed as `media_loader` plugin."""
  loaders = {}
  for media_loader in entry_points(group='media_loader'):
    try:
      loader_module = media_loader.load()
      for name, obj in inspect.getmembers(loader_module):
        if inspect.isclass(obj) and issubclass(obj, base_loader.BaseLoader):
          loaders[obj.alias] = getattr(loader_module, name)
    except ModuleNotFoundError:
      continue
  return loaders


class MediaLoaderService:
  """Handles tasks related to loading tagging results.

  Attributes:
    repo: Repository that contains tagging results.
  """

  def __init__(
    self,
    tagging_results_repository: repositories.BaseTaggingResultsRepository,
  ) -> None:
    """Initializes MediaTaggingService."""
    self.repo = tagging_results_repository

  def load_media_tags(
    self,
    loader_type: str,
    media_type: str,
    location: os.PathLike[str] | str,
    loader_parameters: dict[str, str] | None = None,
  ) -> None:
    """Tags media based on requested tagger.

    Args:
      loader_type: Type of loader to use.
      media_type: Type of media.
      location: Location of tagging results.
      loader_parameters: Additional parameters to use during tagging.
    """
    self._process_media(
      'tag',
      loader_type,
      media_type,
      location,
      loader_parameters,
    )

  def load_media_descriptions(
    self,
    loader_type: str,
    media_type: str,
    location: os.PathLike[str] | str,
    loader_parameters: dict[str, str] | None = None,
  ) -> None:
    """Describes media based on requested tagger.

    Args:
      loader_type: Type of loader to use.
      media_type: Type of media.
      location: Location of tagging results.
      loader_parameters: Additional parameters to use during tagging.
    """
    self._process_media(
      'describe',
      loader_type,
      media_type,
      location,
      loader_parameters,
    )

  def _process_media(
    self,
    action: Literal['tag', 'describe'],
    loader_type: str,
    media_type: str,
    location: os.PathLike[str] | str,
    loader_parameters: dict[str, str] | None = None,
  ) -> None:
    """Gets media information based on tagger and output type.

    Args:
      action: Defines output of tagging: tags or description.
      loader_type: Type of loader to use.
      media_type: Type of media.
      location: Location of tagging results.
      loader_parameters: Additional parameters to use during tagging.

    Raises:
      InvalidMediaTypeError: When incorrect media type is provided.
      TaggerError: When incorrect tagger_type is used.
      MediaTaggerLoaderError: When incorrect loader is specified.
    """
    try:
      media_type_enum = media.MediaTypeEnum[media_type.upper()]
    except KeyError as e:
      raise media.InvalidMediaTypeError(media_type) from e
    if not loader_parameters:
      loader_parameters = {}
    if not loader_type:
      raise base_loader.MediaTaggerLoaderError('No loader specified')
    loaders = _get_loaders()
    if not (loader_class := loaders.get(loader_type)):
      raise base_loader.MediaTaggerLoaderError(
        f'Unsupported type of loader {loader_type}. '
        f'Supported loaders: {list(loaders.keys())}'
      )
    tagging_results = loader_class().load(
      output=action,
      media_type=media_type_enum,
      location=location,
      **loader_parameters,
    )
    if self.repo:
      loader_media_names = {media.identifier for media in tagging_results}
      loaded_media = self.repo.get(
        loader_media_names, media_type, 'loader', action
      )
      not_loaded_media = set(tagging_results).difference(loaded_media)
      self.repo.add(not_loaded_media)
