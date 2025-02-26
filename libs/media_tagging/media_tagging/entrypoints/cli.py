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
import sys

from garf_executors.entrypoints import utils as garf_utils
from garf_io import writer as garf_writer

import media_tagging
from media_tagging import (
  media,
  media_tagging_service,
  repositories,
  tagging_result,
)


def main():
  """Main entrypoint."""
  parser = argparse.ArgumentParser()
  parser.add_argument(
    'action',
    nargs='?',
    choices=['tag', 'describe'],
    help='Action to perform',
    default='tag',
  )
  parser.add_argument(
    'media_paths', nargs='*', help='Paths to local/remote files or URLs'
  )
  parser.add_argument(
    '--media-type',
    dest='media_type',
    choices=media.MediaTypeEnum.options(),
    help='Type of media.',
  )
  parser.add_argument(
    '--tagger',
    dest='tagger',
    choices=list(media_tagging_service.TAGGERS.keys()),
    default='gemini',
    help='Type of tagger',
  )
  parser.add_argument('--writer', dest='writer', default='json')
  parser.add_argument('--output', dest='output', default='tagging_results')
  parser.add_argument(
    '--no-output',
    dest='no_output',
    action='store_true',
    help='Skip writing tagging results',
  )
  parser.add_argument(
    '--db-uri',
    dest='db_uri',
    help='Database connection string to store and retrieve tagging results',
  )
  parser.add_argument('--loglevel', dest='loglevel', default='INFO')
  parser.add_argument('--no-parallel', dest='parallel', action='store_false')
  parser.add_argument(
    '--parallel-threshold',
    dest='parallel_threshold',
    default=10,
    type=int,
    help='Number of parallel processes to perform media tagging',
  )
  parser.add_argument('-v', '--version', dest='version', action='store_true')
  parser.set_defaults(parallel=True)
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(f'media-tagger version: {media_tagging.__version__}')
    sys.exit()
  tagging_service = media_tagging_service.MediaTaggingService(
    repositories.SqlAlchemyTaggingResultsRepository(args.db_uri)
  )
  extra_parameters = garf_utils.ParamsParser(['tagger', args.writer]).parse(
    kwargs
  )

  logging.basicConfig(
    format='[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
    level=args.loglevel,
    datefmt='%Y-%m-%d %H:%M:%S',
  )
  logging.getLogger(__file__)

  parameters = {
    'tagger_type': args.tagger,
    'media_type': args.media_type,
    'media_paths': args.media_paths,
    'tagging_parameters': extra_parameters.get('tagger'),
    'parallel_threshold': args.parallel_threshold,
  }
  if args.action == 'tag':
    tagging_results = tagging_service.tag_media(**parameters)
  else:
    tagging_results = tagging_service.describe_media(**parameters)
  if args.no_output:
    sys.exit()
  report = tagging_result.convert_tagging_results_to_garf_report(
    tagging_results
  )
  writer_parameters = extra_parameters.get(args.writer) or {}
  garf_writer.create_writer(args.writer, **writer_parameters).write(
    report, args.output
  )


if __name__ == '__main__':
  main()
