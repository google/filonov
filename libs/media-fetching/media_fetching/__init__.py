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

"""Fetches media data from various sources."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

from media_fetching.media_fetching_service import MediaFetchingService
from media_fetching.sources.dbm import BidManagerFetchingParameters
from media_fetching.sources.fake import FakeFetchingParameters
from media_fetching.sources.file import FileFetchingParameters
from media_fetching.sources.googleads import GoogleAdsFetchingParameters
from media_fetching.sources.sql import (
  BigQueryFetchingParameters,
  SqlAlchemyQueryFetchingParameters,
)
from media_fetching.sources.youtube import YouTubeFetchingParameters

__all__ = [
  'MediaFetchingService',
]

INPUT_MAPPING = {
  'googleads': GoogleAdsFetchingParameters,
  'youtube': YouTubeFetchingParameters,
  'file': FileFetchingParameters,
  'sqldb': SqlAlchemyQueryFetchingParameters,
  'bq': BigQueryFetchingParameters,
  'fake': FakeFetchingParameters,
  'dbm': BidManagerFetchingParameters,
}
__version__ = '0.5.0'
