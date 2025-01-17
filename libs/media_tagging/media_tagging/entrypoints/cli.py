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
"""Provides CLI for media tagging."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import argparse
import logging

from garf_executors.entrypoints import utils as garf_utils

from media_tagging import media_tagging_service, repositories, tagger, writer

AVAILABLE_TAGGERS = list(tagger.TAGGERS.keys())


def main():
  """Main entrypoint."""
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'media_paths', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--tagger',
    dest='tagger',
    help=f'Tagger type, on of the following: {AVAILABLE_TAGGERS}',
  )
  parser.add_argument('--writer', dest='writer', default='json')
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store and retrieve tagging results',
  )
  parser.add_argument('--output-to-file', dest='output', default=None)
  parser.add_argument('--loglevel', dest='loglevel', default='INFO')
  parser.add_argument('--no-parallel', dest='parallel', action='store_false')
  parser.add_argument(
    '--parallel-threshold',
    dest='parallel_threshold',
    default=10,
    type=int,
    help='Number of parallel processes to perform media tagging',
  )
  parser.set_defaults(parallel=True)
  args, kwargs = parser.parse_known_args()

  tagging_service = media_tagging_service.MediaTaggingService(
    repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
  )
  tagging_parameters = garf_utils.ParamsParser(['tagger']).parse(kwargs)

  logging.basicConfig(
    format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
    level=args.loglevel,
    datefmt='%Y-%m-%d %H:%M:%S',
  )
  logging.getLogger(__file__)

  tagging_results = tagging_service.tag_media(
    tagger_type=args.tagger,
    media_paths=args.media_paths,
    tagging_parameters=tagging_parameters.get('tagger'),
    parallel_threshold=args.parallel_threshold,
  )
  if output := args.output:
    concrete_writer = writer.create_writer(args.writer)
    concrete_writer.write(tagging_results, output)


if __name__ == '__main__':
  main()
