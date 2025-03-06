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

"""CLI utility for loading tagging results to DB."""

import argparse
import logging

from garf_executors.entrypoints import utils as garf_utils

from media_tagging import media, repositories
from media_tagging.loaders import media_loader_service


def main():
  """Main entrypoint."""
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'location', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--action',
    dest='action',
    choices=['tag', 'describe'],
    help='Action to perform',
    default='tag',
  )
  parser.add_argument(
    '--loader',
    dest='loader',
    # choices=list(media_loader_service.LOADERS.keys()),
    default='file',
    help='Type of loader',
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=media.MediaTypeEnum.options(),
    help='Type of media.',
  )
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store tagging results',
  )
  parser.add_argument('--loglevel', dest='loglevel', default='INFO')
  args, kwargs = parser.parse_known_args()

  loader_service = media_loader_service.MediaLoaderService(
    repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
  )
  extra_parameters = garf_utils.ParamsParser(['loader']).parse(kwargs)

  logging.basicConfig(
    format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
    level=args.loglevel,
    datefmt='%Y-%m-%d %H:%M:%S',
  )
  logging.getLogger(__file__)

  for location in args.location:
    parameters = {
      'loader_type': args.loader,
      'media_type': args.media_type,
      'location': location,
      'loader_parameters': extra_parameters.get('loader'),
    }
    if args.action == 'tag':
      loader_service.load_media_tags(**parameters)
    else:
      loader_service.load_media_descriptions(**parameters)


if __name__ == '__main__':
  main()
