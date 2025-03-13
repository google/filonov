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

"""Interface for defining tagging results loaders."""

import abc
import os

from media_tagging import exceptions, media, tagging_result


class MediaTaggerLoaderError(exceptions.MediaTaggingError):
  """Defines generic error for all loaders."""


class BaseLoader(abc.ABC):
  """Interface for defining tagging results loaders."""

  @abc.abstractmethod
  def load(
    self,
    media_type: media.MediaTypeEnum | str,
    location: os.PathLike[str] | str,
    output: str,
    **kwargs: str,
  ) -> list[tagging_result.TaggingResult]:
    """Method for loading tagging results.

    Args:
      media_type: Type of media found in location.
      location: Location of tagging results.
      output: Type of media tagging results (tag or description).
      kwargs: Optional arguments to fine-tune the loading.
    """
